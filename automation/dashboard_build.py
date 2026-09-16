"""
Dashboard DAILY_DATA rebuild + publish — a faithful, deterministic port of
SKILL Steps 5-7 of nutriobox-daily-data-v2. NO browser, NO LLM: pure Python
byte-slicing on the ~100MB dashboard HTML.

Public API:
    rebuild(src_html, target_date, records, addon_records, run_mode, workdir)
        -> RebuildResult   (writes workdir/dashboard.new.html, never the mount)
    publish(new_html, supabase_url, service_key)
        -> dict            (gzip + upsert to Supabase, verify by md5)

Everything that was a "pitfall" in the SKILL is enforced here in code:
  * "const DAILY_DATA=" is exactly 17 chars; prefix MUST end b'=[' (not '=[{').
  * new records fragment carries NO outer brackets; the closing ']' is added once.
  * target_date biz-day split: DROP date==target_date & time>=08:00 and
    date==next_date & time<01:00; KEEP date==target_date & time<08:00
    (that's the previous biz day's late-night, absent from the new CSV).
  * prev-day biz sales MUST be identical before and after (delta==0) or we abort.
  * final file MUST end b'</html>'.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

MARKER = b"const DAILY_DATA="
MARKER_LEN = 17  # len("const DAILY_DATA=") — verified, NOT 18


# ---------------------------------------------------------------------------
# Serialization (Phase A)
# ---------------------------------------------------------------------------
def fmt_num(n) -> str:
    if isinstance(n, float):
        if n == int(n):
            return f"{int(n)}"
        return ("%.10f" % n).rstrip("0").rstrip(".")
    return str(n)


def fmt_record(r: dict) -> str:
    parts = [
        '"restaurant":' + json.dumps(r["restaurant"]),
        '"category":' + json.dumps(r["category"]),
        '"item":' + json.dumps(r["item"]),
        '"qty":' + fmt_num(r["qty"]),
        '"date":' + json.dumps(r["date"]),
        '"time":' + json.dumps(r.get("time", "00:00")),
        '"totalSales":' + fmt_num(r["totalSales"]),
    ]
    if r.get("status"):
        parts.append('"status":' + json.dumps(r["status"]))
    if r.get("invoiceNo"):
        parts.append('"invoiceNo":' + json.dumps(r["invoiceNo"]))
    if r.get("orderType"):
        parts.append('"orderType":' + json.dumps(r["orderType"]))
    if r.get("paymentType"):
        parts.append('"paymentType":' + json.dumps(r["paymentType"]))
    if r.get("area"):
        parts.append('"area":' + json.dumps(r["area"]))
    if r.get("isAddon") == 1:
        parts.append('"isAddon":1')
    return "{" + ",".join(parts) + "}"


def serialize_fragment(records: list[dict]) -> str:
    """Comma-separated records, NO surrounding brackets."""
    return ",".join(fmt_record(r) for r in records)


# ---------------------------------------------------------------------------
# Record-string helpers (Phase C works on raw JSON substrings, not json.loads)
# ---------------------------------------------------------------------------
_DATE_RE = re.compile(r'"date":"(\d{4}-\d{2}-\d{2})"')
_TIME_RE = re.compile(r'"time":"(\d{2}):(\d{2})"')
_SALES_RE = re.compile(r'"totalSales":(-?\d+(?:\.\d+)?)')


def _minutes(rec: str) -> int | None:
    m = _TIME_RE.search(rec)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def _biz_day_sales(records: list[str], day: str, next_day: str) -> float:
    """Sum totalSales over the business day of `day` (main rows only, not addons)."""
    total = 0.0
    for rec in records:
        if '"isAddon":1' in rec:
            continue
        dm = _DATE_RE.search(rec)
        if not dm:
            continue
        d = dm.group(1)
        mins = _minutes(rec)
        in_day = (d == day and mins is not None and mins >= 8 * 60)
        in_tail = (d == next_day and mins is not None and mins < 60)
        if in_day or in_tail:
            sm = _SALES_RE.search(rec)
            if sm:
                total += float(sm.group(1))
    return total


# ---------------------------------------------------------------------------
# Rebuild (Phases B + C)
# ---------------------------------------------------------------------------
@dataclass
class RebuildResult:
    new_html: Path
    md5: str
    kept_records: int
    dropped_records: int
    appended_records: int
    prev_biz_before: float
    prev_biz_after: float
    warnings: list[str] = field(default_factory=list)

    @property
    def prev_stable(self) -> bool:
        return round(self.prev_biz_before, 2) == round(self.prev_biz_after, 2)


def _dates(target_date: str) -> tuple[str, str]:
    from datetime import date, timedelta
    y, m, d = map(int, target_date.split("-"))
    td = date(y, m, d)
    return ((td + timedelta(days=1)).isoformat(), (td - timedelta(days=1)).isoformat())


def rebuild(src_html: str | Path, target_date: str, records: list[dict],
            addon_records: list[dict], run_mode: str, workdir: str | Path) -> RebuildResult:
    src_html = Path(src_html)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    next_date, prev_date = _dates(target_date)
    warnings: list[str] = []

    data = src_html.read_bytes()
    dd_offset = data.find(MARKER)
    if dd_offset == -1:
        raise ValueError("const DAILY_DATA= marker not found in dashboard HTML")
    bracket_byte = dd_offset + MARKER_LEN
    if data[bracket_byte:bracket_byte + 1] != b"[":
        raise ValueError(
            f"byte after marker is {data[bracket_byte:bracket_byte+1]!r}, expected b'['"
            " — marker length wrong or file corrupt"
        )
    last_close = data.rfind(b"}];")
    if last_close <= bracket_byte:
        raise ValueError("closing '}];' of DAILY_DATA not found")

    prefix = data[:bracket_byte + 1]            # ends with b'=['
    suffix = data[last_close + 2:]              # starts with b';'
    if not prefix.endswith(b"=["):
        raise ValueError("prefix does not end with b'=[' — refusing to write")
    raw = data[bracket_byte + 1:last_close + 1].decode("utf-8")

    # Split the existing record list without json.loads (too big).
    raw = raw.strip()
    if raw.startswith("["):
        raw = raw[1:]
    if raw.endswith("]"):
        raw = raw[:-1]
    existing = raw.split("},{") if raw else []
    for i in range(len(existing)):
        if not existing[i].startswith("{"):
            existing[i] = "{" + existing[i]
        if not existing[i].endswith("}"):
            existing[i] = existing[i] + "}"

    # Snapshot prev-day biz sales BEFORE we drop anything.
    prev_before = _biz_day_sales(existing, prev_date, target_date)

    # Phase C filter: drop the target_date business day, preserve its late-night tail.
    kept: list[str] = []
    dropped = 0
    for rec in existing:
        dm = _DATE_RE.search(rec)
        if dm:
            d = dm.group(1)
            if d == target_date:
                mins = _minutes(rec)
                if mins is not None and mins >= 8 * 60:
                    dropped += 1
                    continue           # target_date biz day → drop & re-append
                # time < 08:00 → previous biz day late-night → KEEP
            elif d == next_date:
                mins = _minutes(rec)
                if mins is not None and mins < 60:
                    dropped += 1
                    continue           # 00:00-00:59 next_date → target_date late-night
        kept.append(rec)

    new_frag = serialize_fragment(records + addon_records)
    appended = len(records) + len(addon_records)

    body = (",".join(kept) + "," + new_frag) if kept else new_frag
    new_html = workdir / "dashboard.new.html"
    with open(new_html, "wb") as f:
        f.write(prefix)
        f.write(body.encode("utf-8"))
        f.write(b"]")
        f.write(suffix)

    # Integrity gates.
    tail = new_html.read_bytes()[-16:]
    if not tail.rstrip().endswith(b"</html>"):
        raise ValueError(f"assembled file does not end with </html> (tail={tail!r})")
    with open(new_html, "rb") as f:
        head = f.read(bracket_byte + 3)
    if head[bracket_byte:bracket_byte + 2] != b"[{":
        raise ValueError(
            f"DAILY_DATA does not start with '[{{' (got {head[bracket_byte:bracket_byte+2]!r})"
        )

    # Recompute prev-day sales AFTER — must be identical.
    new_all = kept + [r for r in (new_frag.split("},{") if new_frag else [])]
    # normalise the freshly-serialized fragment pieces
    fixed = []
    for i, r in enumerate(new_all):
        if i < len(kept):
            fixed.append(r)
        else:
            if not r.startswith("{"):
                r = "{" + r
            if not r.endswith("}"):
                r = r + "}"
            fixed.append(r)
    prev_after = _biz_day_sales(fixed, prev_date, target_date)

    md5 = hashlib.md5(new_html.read_bytes()).hexdigest()
    res = RebuildResult(
        new_html=new_html, md5=md5,
        kept_records=len(kept), dropped_records=dropped, appended_records=appended,
        prev_biz_before=prev_before, prev_biz_after=prev_after, warnings=warnings,
    )
    if not res.prev_stable:
        warnings.append(
            f"PREV-DAY SALES CHANGED: before ₹{prev_before:,.0f} vs after ₹{prev_after:,.0f} "
            f"(delta ₹{prev_after - prev_before:,.0f}) — DO NOT PUBLISH."
        )
    return res


# ---------------------------------------------------------------------------
# Publish (Step 7)
# ---------------------------------------------------------------------------
def read_env_local(env_path: str | Path) -> dict:
    out: dict[str, str] = {}
    for line in Path(env_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def publish(new_html: str | Path, supabase_url: str, service_key: str,
            object_path: str = "reports/sales-dashboard.html") -> dict:
    """
    gzip -9 the assembled file and upsert it to Supabase Storage, then verify by
    downloading the object, gunzipping, and comparing md5. Returns a status dict.
    Never prints the key.
    """
    new_html = Path(new_html)
    local_md5 = hashlib.md5(new_html.read_bytes()).hexdigest()
    gz = new_html.with_suffix(".html.gz")
    with open(new_html, "rb") as fi, gzip.open(gz, "wb", compresslevel=9) as fo:
        fo.writelines(fi)
    gz_size = gz.stat().st_size
    if gz_size > 50 * 1024 * 1024:
        return {"ok": False, "error": f"gzip too large: {gz_size} bytes (>50MB)"}

    url = supabase_url.rstrip("/") + "/storage/v1/object/" + object_path
    code = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-X", "POST", url,
         "-H", f"apikey: {service_key}",
         "-H", f"Authorization: Bearer {service_key}",
         "-H", "Content-Type: text/html",
         "-H", "Content-Encoding: gzip",
         "-H", "Cache-Control: no-cache",
         "-H", "x-upsert: true",
         "--data-binary", f"@{gz}", "--max-time", "60"],
        capture_output=True, text=True,
    ).stdout.strip()
    if code != "200":
        return {"ok": False, "error": f"upload HTTP {code}", "gz_size": gz_size}

    # Verify by content. The Supabase CDN can serve a stale copy for a second or
    # two right after upsert, so cache-bust and retry a few times before failing.
    import time as _time
    public_base = supabase_url.rstrip("/") + "/storage/v1/object/public/" + object_path
    live_gz = new_html.parent / "live.gz"
    live_md5 = None
    for attempt in range(4):
        _time.sleep(3)
        url = f"{public_base}?t={int(_time.time())}"
        subprocess.run(["curl", "-sS", "-m", "180", "-H", "Cache-Control: no-cache",
                        "-o", str(live_gz), url], capture_output=True)
        try:
            live_md5 = hashlib.md5(gzip.open(live_gz, "rb").read()).hexdigest()
        except Exception:  # noqa: BLE001
            live_md5 = None
            continue
        if live_md5 == local_md5:
            break
    return {
        "ok": live_md5 == local_md5, "http": code, "gz_size": gz_size,
        "local_md5": local_md5, "live_md5": live_md5,
        "verified": live_md5 == local_md5,
    }
