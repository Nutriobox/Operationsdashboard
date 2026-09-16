"""
Weekly delivery-delay dashboard — deterministic port of the Cowork task
`nutriobox-weekly-delay-dashboard`. NO browser, NO LLM.

  python delay_dashboard.py --selftest   re-fetch the newest week ALREADY in the
                                         dashboard and prove it matches byte-for-byte
  python delay_dashboard.py --dry-run    fetch + show exactly what would be appended
  python delay_dashboard.py              live: append, write both copies, publish
  python delay_dashboard.py --week 2026-08-10        target a specific week (its Monday)
  python delay_dashboard.py --no-publish             update files, skip Supabase
  python delay_dashboard.py --login                  sign the browser profile into Google

Reads the Weekly Sales sheet with **Playwright** (sheet_browser.py), driving the
same persistent profile refresh_tokens.py maintains — no service-account key to
manage. `--reader sheets` switches to the Sheets API instead, and
`--reader both` runs BOTH and asserts they agree cell-for-cell, which is how the
browser reader is validated.

The two guards from the SKILL are kept, because they caught real bugs:
  Guard A — the target tab must exist, matched EXACTLY. Never fuzzy-match.
  Guard B — the fetched block must differ from the last week already in the
            dashboard. Identical data means we read the wrong tab.
A third guard is added here:
  Guard C — every outlet must be found and every value must parse. A partial
            week is never appended; we abort with the list of misses.

Weeks run Monday -> Sunday. Never Sunday -> Saturday.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import config
from dashboard_build import read_env_local

IST = timezone(timedelta(hours=5, minutes=30))

# --- where things live ------------------------------------------------------
SHEET_ID = "1oNCCGX5ntgPW_OYwjWB5LMFhLfPitxzVAMWj95G0qpc"   # Weekly Sales
REPORTS_DIR = Path(r"C:\Users\hp\Downloads\NutrioBox_Reports")
PRIMARY = REPORTS_DIR / "nutriobox_delay_dashboard_v3.html"
DEPLOY_COPY = REPORTS_DIR / "Application" / "nutriobox_delay_dashboard_v3.html"
OBJECT_PATH = "reports/delay-dashboard.html"

# Column A label in the sheet -> outlet key in the dashboard's `data` object.
# The sheet's spelling has drifted before, so match case-insensitively on the
# LEFT and keep the RIGHT exactly as the HTML has it.
OUTLETS = [
    "DLF - Phase 2",
    "Rajinder Nagar",
    "Noida 63",
    "Dwarka",
    "Janakpuri",
    "Karkardooma",
    "Noida - Advant",
    "Rohini",
    "Sector 15 - GGN",
    "Shivalik",
]

# Columns T,U,V,W = orders, avg delivery mins, >25 min count, >25 min %.
COL_FIRST, COL_LAST = "T", "W"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------------------------------------------------------------------------
# Week naming
# ---------------------------------------------------------------------------
def last_complete_week(today: date | None = None) -> tuple[date, date]:
    """Most recent fully-finished Monday->Sunday week."""
    today = today or datetime.now(IST).date()
    this_monday = today - timedelta(days=today.weekday())
    monday = this_monday - timedelta(days=7)
    return monday, monday + timedelta(days=6)


def tab_name(mon: date, sun: date) -> str:
    """'Aug 10 - Aug 16, 2026' — always both months, always the year."""
    return (f"{MONTHS[mon.month - 1]} {mon.day} - "
            f"{MONTHS[sun.month - 1]} {sun.day}, {sun.year}")


def week_label(mon: date, sun: date) -> str:
    """'Aug 10-16' same month, 'Jun 29-Jul 5' across months."""
    if mon.month == sun.month:
        return f"{MONTHS[mon.month - 1]} {mon.day}-{sun.day}"
    return (f"{MONTHS[mon.month - 1]} {mon.day}-"
            f"{MONTHS[sun.month - 1]} {sun.day}")


def heading_range(mon: date, sun: date) -> str:
    """'Aug 10 - Aug 16' for the All Outlets Comparison <h3>."""
    return (f"{MONTHS[mon.month - 1]} {mon.day} - "
            f"{MONTHS[sun.month - 1]} {sun.day}")


def subtitle_end(sun: date) -> str:
    return f"{MONTHS[sun.month - 1]} {sun.day}, {sun.year}"


# ---------------------------------------------------------------------------
# Sheet fetch
# ---------------------------------------------------------------------------
def _num(v, where: str) -> float:
    """'1,030.00' -> 1030.0. Blank/'-'/'#DIV/0!' is an error, not a zero."""
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("%", "")
    if not s or s in {"-", "—", "N/A"} or s.startswith("#"):
        raise ValueError(f"{where}: non-numeric value {v!r}")
    return float(s)


def _tidy(n: float):
    """Match the HTML's style: ints stay ints, floats keep their decimals."""
    return int(n) if float(n).is_integer() else round(float(n), 2)


class ApiReader:
    """Sheets-API reader. Kept as a cross-check for the browser reader."""

    def __enter__(self):
        from sheets import Sheets
        self.sh = Sheets()
        return self

    def __exit__(self, *exc):
        pass

    def tab_titles(self, sheet_id):
        return self.sh.tab_titles(sheet_id)

    def rows(self, sheet_id, tab):
        from sheets import a1
        return self.sh.read_range(sheet_id, a1(tab, f"A1:{COL_LAST}200"))


def make_reader(kind: str):
    if kind == "sheets":
        return ApiReader()
    from sheet_browser import BrowserReader
    return BrowserReader()


def fetch_week(reader, tab: str) -> dict[str, list]:
    """{outlet: [T,U,V,W]} for all 10 outlets. Guards A and C live here."""
    # Guard A — exact tab match, ALWAYS, for both readers. For the browser
    # reader this is load-bearing: gviz?sheet=<name> silently returns a
    # DIFFERENT sheet when the name doesn't match, so a fuzzy match here would
    # append another week's numbers under today's label.
    titles = reader.tab_titles(SHEET_ID)
    if tab not in titles:
        near = [t for t in titles if tab.split(" - ")[0] in t]
        raise SystemExit(
            f"ABORT (Guard A): tab {tab!r} does not exist in the Weekly Sales sheet.\n"
            f"  The week has not been added yet — nothing to append.\n"
            + (f"  Similar tabs present: {near}\n" if near else "")
        )

    rows = reader.rows(SHEET_ID, tab)
    ti = ord(COL_FIRST) - ord("A")          # 19
    wi = ord(COL_LAST) - ord("A")           # 22

    by_label = {}
    for r in rows:
        if not r or not str(r[0]).strip():
            continue
        by_label.setdefault(str(r[0]).strip().lower(), r)

    out, missing, bad = {}, [], []
    for name in OUTLETS:
        row = by_label.get(name.lower())
        if row is None:
            missing.append(name)
            continue
        if len(row) <= wi:
            bad.append(f"{name}: row stops at column {chr(ord('A') + len(row) - 1)}")
            continue
        try:
            out[name] = [_tidy(_num(row[i], f"{name} col {chr(ord('A') + i)}"))
                         for i in range(ti, wi + 1)]
        except ValueError as e:
            bad.append(str(e))

    # Guard C — all or nothing.
    if missing or bad:
        raise SystemExit(
            "ABORT (Guard C): the week is incomplete, refusing to append a partial row.\n"
            + ("".join(f"  missing outlet: {m}\n" for m in missing))
            + ("".join(f"  bad value: {b}\n" for b in bad))
            + f"  Check tab {tab!r} in the Weekly Sales sheet."
        )
    return out


# ---------------------------------------------------------------------------
# HTML parse / rewrite
# ---------------------------------------------------------------------------
@dataclass
class Dashboard:
    text: str
    weeks: list[str]
    data: dict[str, list[list]]
    weeks_span: tuple[int, int]      # slice bounds of the [...] after `const weeks =`
    data_span: tuple[int, int]       # slice bounds of the {...} after `const data =`


def _match_bracket(s: str, start: int) -> int:
    """Index just past the bracket opened at `start`. String-aware."""
    opener = s[start]
    closer = {"[": "]", "{": "}"}[opener]
    depth, i, quote = 0, start, None
    while i < len(s):
        c = s[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError(f"unbalanced {opener} from offset {start}")


def load(path: Path) -> Dashboard:
    return parse(path.read_text(encoding="utf-8"), str(path))


def parse(text: str, where: str = "<memory>") -> Dashboard:
    m = re.search(r"const\s+weeks\s*=\s*", text)
    if not m:
        raise SystemExit(f"ABORT: `const weeks =` not found in {where}")
    ws = text.index("[", m.end())
    we = _match_bracket(text, ws)
    weeks = re.findall(r'"([^"]*)"', text[ws:we])

    m = re.search(r"const\s+data\s*=\s*", text)
    if not m:
        raise SystemExit(f"ABORT: `const data =` not found in {where}")
    ds = text.index("{", m.end())
    de = _match_bracket(text, ds)

    data: dict[str, list[list]] = {}
    body = text[ds:de]
    for om in re.finditer(r'"([^"]+)"\s*:\s*\[', body):
        key = om.group(1)
        arr_start = om.end() - 1
        arr_end = _match_bracket(body, arr_start)
        data[key] = [
            [float(x) if "." in x else int(x) for x in tup.split(",")]
            for tup in re.findall(r"\[([^\[\]]*)\]", body[arr_start:arr_end])
        ]
    return Dashboard(text, weeks, data, (ws, we), (ds, de))


def _fmt_tuple(vals: list) -> str:
    return "[" + ",".join(str(v) for v in vals) + "]"


def append_week(dash: Dashboard, label: str, week: dict[str, list],
                mon: date, sun: date) -> str:
    """Return the new file text. Pure string work; nothing is written here."""
    # 1. weeks array — rebuild it wrapped the way the file already has it.
    new_weeks = dash.weeks + [label]
    weeks_src = ("[\n  " + ",".join(f'"{w}"' for w in new_weeks) + "\n]")

    # 2. data object — append one tuple per outlet, on its own line so the diff
    #    stays readable (the file already mixes packed and one-per-line rows).
    body = dash.text[dash.data_span[0]:dash.data_span[1]]
    for name in OUTLETS:
        om = re.search(r'"' + re.escape(name) + r'"\s*:\s*\[', body)
        if not om:
            raise SystemExit(f"ABORT: outlet {name!r} not present in `const data`")
        arr_start = om.end() - 1
        arr_end = _match_bracket(body, arr_start)
        inner = body[arr_start + 1:arr_end - 1].rstrip()
        inner = f"{inner},\n    {_fmt_tuple(week[name])}\n  "
        body = body[:arr_start] + "[" + inner + "]" + body[arr_end:]

    text = (dash.text[:dash.data_span[0]] + body + dash.text[dash.data_span[1]:])
    # weeks sits before data, so splice it after and use the ORIGINAL offsets.
    text = text[:dash.weeks_span[0]] + weeks_src + text[dash.weeks_span[1]:]

    # 3. subtitle: "... to Aug 16, 2026 (26 Weeks)"
    text, n = re.subn(
        r"(Weekly KOT Report &mdash;\s*[A-Z][a-z]{2} \d{1,2}, \d{4} to )"
        r"[A-Z][a-z]{2} \d{1,2}, \d{4}\s*\(\d+ Weeks?\)",
        lambda m: f"{m.group(1)}{subtitle_end(sun)} ({len(new_weeks)} Weeks)",
        text, count=1,
    )
    if n != 1:
        raise SystemExit("ABORT: could not update the subtitle line")

    # 4. heading: "All Outlets Comparison — Latest Week (Aug 10 - Aug 16)"
    text, n = re.subn(
        r"(All Outlets Comparison &mdash; Latest Week \()[^)]*\)",
        lambda m: f"{m.group(1)}{heading_range(mon, sun)})",
        text, count=1,
    )
    if n != 1:
        raise SystemExit("ABORT: could not update the All Outlets Comparison heading")
    return text


def verify(text: str, expect_weeks: int) -> None:
    """SKILL Step 4, enforced in code."""
    dash = parse(text, "the rewritten file")
    if len(dash.weeks) != expect_weeks:
        raise SystemExit(f"ABORT: weeks has {len(dash.weeks)}, expected {expect_weeks}")
    for name, rows in dash.data.items():
        if len(rows) != expect_weeks:
            raise SystemExit(
                f"ABORT: {name} has {len(rows)} data points but weeks has {expect_weeks}")
    if not text.rstrip().endswith("</html>"):
        raise SystemExit("ABORT: file does not end with </html> — truncated mid-script")


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------
def publish(path: Path, supabase_url: str, service_key: str) -> dict:
    """
    Upsert as PLAIN HTML. The delay object is NOT gzipped — adding
    Content-Encoding here serves a broken page.
    """
    url = supabase_url.rstrip("/") + "/storage/v1/object/" + OBJECT_PATH
    code = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-X", "POST", url,
         "-H", f"apikey: {service_key}",
         "-H", f"Authorization: Bearer {service_key}",
         "-H", "Content-Type: text/html",
         "-H", "Cache-Control: no-cache",
         "-H", "x-upsert: true",
         "--data-binary", f"@{path}", "--max-time", "60"],
        capture_output=True, text=True,
    ).stdout.strip()
    if code != "200":
        return {"ok": False, "error": f"upload HTTP {code}"}

    public = (supabase_url.rstrip("/")
              + "/storage/v1/object/public/" + OBJECT_PATH)
    want = path.read_bytes()
    for _ in range(4):
        time.sleep(3)
        got = subprocess.run(
            ["curl", "-sS", "--max-time", "60", f"{public}?t={int(time.time())}"],
            capture_output=True,
        ).stdout
        if got == want:
            return {"ok": True, "bytes": len(want)}
    return {"ok": False, "error": "uploaded but the public object still differs",
            "bytes": len(want)}


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def selftest(kind: str) -> int:
    """
    Re-fetch the week the dashboard already ends with and compare. This proves
    the sheet layout, the outlet names and the T-W columns are all still right,
    without hard-coding numbers that go stale every week.

    With --reader both, ALSO fetch through the Sheets API and require the two
    readers to agree cell-for-cell. That is what validates the Playwright path:
    if gviz ever falls back to the wrong tab, the two will disagree loudly.
    """
    dash = load(PRIMARY)
    label = dash.weeks[-1]
    print(f"Newest week in the dashboard: {label}")

    mon, sun = None, None
    probe = datetime.now(IST).date()
    for _ in range(60):
        m, s = last_complete_week(probe)
        if week_label(m, s) == label:
            mon, sun = m, s
            break
        probe -= timedelta(days=7)
    if mon is None:
        print(f"  could not map {label!r} back to a Mon-Sun week", file=sys.stderr)
        return 1

    tab = tab_name(mon, sun)
    kinds = ["playwright", "sheets"] if kind == "both" else [kind]
    print(f"Re-fetching tab: {tab}   via {' + '.join(kinds)}\n")

    results = {}
    for k in kinds:
        with make_reader(k) as r:
            results[k] = fetch_week(r, tab)

    live = results[kinds[0]]
    bad = 0
    for name in OUTLETS:
        want = [_tidy(v) for v in dash.data[name][-1]]
        got = live[name]
        ok = want == got
        bad += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] {name:<18} "
              f"dashboard {want}  sheet {got}")

    if len(kinds) > 1:
        print(f"\n  cross-check: {kinds[0]} vs {kinds[1]}")
        a, b = results[kinds[0]], results[kinds[1]]
        for name in OUTLETS:
            ok = a[name] == b[name]
            bad += not ok
            print(f"  [{'OK  ' if ok else 'FAIL'}] {name:<18} "
                  f"{a[name]}  vs  {b[name]}")

    print()
    if bad:
        print(f"{bad} check(s) disagree — do NOT trust a live run. "
              "The sheet layout, an outlet name, or the gviz tab mapping has "
              "changed.", file=sys.stderr)
        return 1
    print("Client is healthy.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="fetch and print what would be appended; write nothing")
    ap.add_argument("--selftest", action="store_true",
                    help="re-fetch the newest week already in the dashboard and compare")
    ap.add_argument("--week", help="Monday of the target week, YYYY-MM-DD "
                                   "(default: last complete Mon-Sun week)")
    ap.add_argument("--no-publish", action="store_true",
                    help="update the local files but skip the Supabase upload")
    ap.add_argument("--reader", choices=["playwright", "sheets", "both"],
                    default="playwright",
                    help="how to read the sheet (default: playwright). "
                         "'both' cross-checks the two against each other.")
    ap.add_argument("--login", action="store_true",
                    help="open a real browser window to sign the profile into Google")
    args = ap.parse_args()

    if args.login:
        from sheet_browser import login
        login(SHEET_ID)
        return 0

    if args.selftest:
        return selftest(args.reader)

    if args.week:
        mon = datetime.strptime(args.week, "%Y-%m-%d").date()
        if mon.weekday() != 0:
            raise SystemExit(f"--week must be a Monday; {args.week} is a "
                             f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][mon.weekday()]}")
        sun = mon + timedelta(days=6)
    else:
        mon, sun = last_complete_week()

    tab, label = tab_name(mon, sun), week_label(mon, sun)
    mode = "DRY RUN — nothing will be written" if args.dry_run else "LIVE"
    print(f"NutrioBox weekly delay dashboard")
    print(f"Mode:   {mode}")
    print(f"Reader: {args.reader}")
    print(f"Week:   {mon} -> {sun}")
    print(f"Tab:    {tab}")
    print(f"Label:  {label}\n")

    dash = load(PRIMARY)
    already = label in dash.weeks
    if already and not args.dry_run:
        print(f"Week {label!r} is already in the dashboard "
              f"(position {dash.weeks.index(label) + 1} of {len(dash.weeks)}). "
              f"Nothing to do.")
        return 0
    if already:
        # A dry run that stops here proves nothing about the reader, which is
        # the whole point of a dry run. Fetch anyway and compare against the
        # row already stored — that is a live check of the whole read path.
        print(f"NOTE: {label!r} is already in the dashboard (position "
              f"{dash.weeks.index(label) + 1} of {len(dash.weeks)}).")
        print("      A live run would stop here. Fetching anyway to exercise "
              "the reader.\n")
        idx = dash.weeks.index(label)
        dash = parse(dash.text)
        dash.weeks = dash.weeks[:idx]
        for k in dash.data:
            dash.data[k] = dash.data[k][:idx]

    if args.reader == "both":
        with make_reader("playwright") as r:
            week = fetch_week(r, tab)
        with make_reader("sheets") as r:
            other = fetch_week(r, tab)
        if week != other:
            diffs = [f"    {n}: playwright {week[n]} vs sheets {other[n]}"
                     for n in OUTLETS if week[n] != other[n]]
            raise SystemExit("ABORT: the two readers disagree — refusing to write.\n"
                             + "\n".join(diffs))
        print("cross-check: both readers agree\n")
    else:
        with make_reader(args.reader) as r:
            week = fetch_week(r, tab)

    # Guard B — identical to the previous week means we read the wrong tab.
    prev = {n: [_tidy(v) for v in dash.data[n][-1]] for n in OUTLETS}
    if all(prev[n] == week[n] for n in OUTLETS):
        raise SystemExit(
            "ABORT (Guard B): every outlet's [T,U,V,W] is identical to "
            f"{dash.weeks[-1]!r}. That is a fallback/duplicate read, not a new "
            "week. Nothing was written.")

    print(f"{'Outlet':<18} {'Orders':>7} {'AvgMin':>7} {'>25':>6} {'>25%':>7}   "
          f"(prev week)")
    for n in OUTLETS:
        t, u, v, w = week[n]
        pt, pu, pv, pw = prev[n]
        print(f"{n:<18} {t:>7} {u:>7} {v:>6} {w:>7}   "
              f"({pt}, {pu}, {pv}, {pw})")

    worst = max(OUTLETS, key=lambda n: week[n][2])
    jump = max(OUTLETS, key=lambda n: week[n][3] - prev[n][3])
    print(f"\nMost >25 min orders: {worst} ({week[worst][2]}, {week[worst][3]}%)")
    print(f"Biggest jump in >25%: {jump} "
          f"({prev[jump][3]}% -> {week[jump][3]}%)")

    if args.dry_run:
        if already:
            stored = load(PRIMARY)
            i = stored.weeks.index(label)
            bad = [n for n in OUTLETS
                   if [_tidy(v) for v in stored.data[n][i]] != week[n]]
            print()
            if bad:
                print(f"MISMATCH against the {label} row already in the dashboard: "
                      f"{', '.join(bad)}", file=sys.stderr)
                print("Do NOT go live — the read path disagrees with known-good data.",
                      file=sys.stderr)
                return 1
            print(f"Fetched week matches the stored {label} row for all "
                  f"{len(OUTLETS)} outlets — read path verified.")
        print("\nDry run — no files touched, nothing published.")
        return 0

    new_text = append_week(dash, label, week, mon, sun)
    verify(new_text, len(dash.weeks) + 1)

    backup = PRIMARY.with_suffix(f".html.bak-{mon:%Y%m%d}")
    shutil.copy2(PRIMARY, backup)
    PRIMARY.write_text(new_text, encoding="utf-8")
    DEPLOY_COPY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PRIMARY, DEPLOY_COPY)
    if PRIMARY.read_bytes() != DEPLOY_COPY.read_bytes():
        raise SystemExit("ABORT: the two local copies differ after the write")
    print(f"\nWrote {PRIMARY} ({PRIMARY.stat().st_size:,} bytes)")
    print(f"Wrote {DEPLOY_COPY} (identical)")
    print(f"Backup {backup.name}")

    if args.no_publish:
        print("\n--no-publish — the live site was NOT updated.")
        return 0

    env = read_env_local(config.ENV_LOCAL)
    res = publish(DEPLOY_COPY, env["NEXT_PUBLIC_SUPABASE_URL"],
                  env["SUPABASE_SERVICE_ROLE_KEY"])
    if not res.get("ok"):
        print(f"\nPUBLISH FAILED: {res.get('error')}", file=sys.stderr)
        print("The local files are correct — re-run with --no-publish removed "
              "once the network/key issue is fixed.", file=sys.stderr)
        return 1
    print(f"\nPublished {OBJECT_PATH} ({res['bytes']:,} bytes) — verified byte-identical.")
    print(f"Live: {config.DASHBOARD_URL}/dashboard/delay")
    return 0


if __name__ == "__main__":
    sys.exit(main())
