"""
nutriobox-daily-data-v2, ported off Claude.

Deterministic Python + one Playwright step (the CSV export) + optional, dormant
Claude-API fallbacks. Same contract as the SKILL, enforced in code.

  python daily_data.py --selftest    prove the moving parts still work; writes nothing
  python daily_data.py --dry-run     full pull + rebuild in /tmp; prints what it WOULD change
  python daily_data.py               live: update local dashboard HTML + publish to Supabase

Run mode is hour-aware (IST): before noon -> yesterday full day; after noon ->
today partial (8 AM -> now). Pass --date YYYY-MM-DD --mode morning|afternoon to override.

Cutover plan: run --dry-run beside the Claude task for a few mornings; when the
totals match, schedule this and disable the Claude `nutriobox-daily-data-v2` task.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
import claude_assist
import dashboard_build as db
from petpooja import Petpooja, ScrapeError, SessionExpired

# Windows consoles default to cp1252, which can't encode the status emoji we
# print (✅ ⚠️ 🌐). Force UTF-8 so output never crashes the run.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

IST = timezone(timedelta(hours=5, minutes=30))
OUTPUTS = config.ROOT / "outputs"
LOGS = config.LOGS

# Where the rolling ~100MB dashboard HTML lives (newest file wins).
REPORTS_DIR = Path(os.environ.get(
    "NUTRIOBOX_REPORTS_DIR", r"C:\Users\hp\Downloads\NutrioBox_Reports"))

RECONCILE_THRESHOLD = 200  # rupees (SKILL Step 2.8)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def log(msg: str = "") -> None:
    print(msg, flush=True)


def newest_dashboard() -> Path:
    files = sorted(REPORTS_DIR.glob("NutrioBox_Dashboard_*.html"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"no NutrioBox_Dashboard_*.html in {REPORTS_DIR}")
    return files[0]


def compute_target(now_ist: datetime) -> tuple[str, str]:
    if now_ist.hour < 12:
        return (now_ist.date() - timedelta(days=1)).strftime("%Y-%m-%d"), "morning"
    return now_ist.date().strftime("%Y-%m-%d"), "afternoon"


# ---------------------------------------------------------------------------
# Step 3: dedupe an exported CSV to invoice level
# ---------------------------------------------------------------------------
def dedupe_csv(csv_path: Path, target_date: str, run_mode: str) -> list[dict]:
    csv.field_size_limit(100_000_000)
    seen: set[tuple[str, str]] = set()
    records: list[dict] = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            restaurant = (row.get("restaurant_name") or "").strip()
            if "Test" in restaurant:
                continue
            status = (row.get("status") or "").strip()
            if status not in ("Success", "Cancelled"):
                continue
            invoice_no = str(row.get("invoice_no") or "").strip()
            if not invoice_no:
                continue
            key = (restaurant, invoice_no)
            if key in seen:
                continue
            seen.add(key)
            category = (row.get("category_name") or "").strip()
            item = (row.get("item_name") or "").strip()
            date_str = (row.get("date") or "").strip()
            if not restaurant or not category or not item or len(date_str) < 16:
                continue
            try:
                qty = float(row.get("item_quantity") or 0)
            except ValueError:
                qty = 0.0
            try:
                invoice_total = float(row.get("total") or 0)
            except ValueError:
                invoice_total = 0.0
            records.append({
                "restaurant": restaurant, "category": category, "item": item,
                "qty": qty, "date": date_str[:10], "time": date_str[11:16],
                "totalSales": invoice_total if status == "Success" else 0,
                "status": status, "invoiceNo": invoice_no,
                "orderType": (row.get("order_type") or "").strip(),
                "paymentType": (row.get("payment_type") or "").strip(),
                "area": (row.get("area") or "").strip(),
            })
    # Afternoon: drop this-morning-before-8AM rows (they belong to prior biz day,
    # already in the dashboard from the previous morning's run).
    if run_mode == "afternoon":
        records = [r for r in records
                   if not (r["date"] == target_date and r["time"] < "08:00")]
    return records


# ---------------------------------------------------------------------------
# Step 4: addons for all 10 outlets (pure HTTP)
# ---------------------------------------------------------------------------
def pull_addons(target_date: str, headless: bool = True) -> tuple[list[dict], list[str]]:
    # Report 31 is JS-rendered, so addons are scraped in the browser (Playwright).
    from browser_export import scrape_addons
    out = scrape_addons(target_date, list(config.OUTLETS.keys()), headless=headless)
    results, errors = out["results"], out["errors"]
    addon_records: list[dict] = []
    warns: list[str] = []
    for oid, name in config.OUTLETS.items():
        for r in results.get(oid, []):
            addon_records.append({
                "restaurant": name,
                "category": "[Add-on] " + r["addonGroup"],
                "item": r["addonItem"],
                "qty": r["qty"],
                "date": target_date, "time": "12:00",
                "totalSales": r["total"], "isAddon": 1,
            })
    for oid, err in errors.items():
        warns.append(f"addon scrape failed for {config.SHORT[oid]}: {err}")
    return addon_records, warns


# ---------------------------------------------------------------------------
# Step 4B: validation gates
# ---------------------------------------------------------------------------
def validate(records: list[dict], addon_records: list[dict], run_mode: str) -> tuple[list[str], bool]:
    warnings: list[str] = []
    outlet = {}
    for r in records:
        o = outlet.setdefault(r["restaurant"], {"count": 0, "sales": 0.0})
        o["count"] += 1
        if r["status"] == "Success":
            o["sales"] += r["totalSales"]

    if len(outlet) < 10:
        warnings.append(f"MISSING OUTLETS: {len(outlet)}/10 present")
    for name, d in outlet.items():
        if d["count"] < 5:
            warnings.append(f"LOW COUNT: {name} has {d['count']} invoices")
        if d["sales"] == 0:
            warnings.append(f"ZERO SALES: {name}")

    total_inv = len(records)
    total_sales = sum(r["totalSales"] for r in records if r["status"] == "Success")
    if run_mode == "morning":
        if total_inv < 800:
            warnings.append(f"LOW TOTAL: {total_inv} invoices (full day, expect 1000+)")
        if total_sales < 400_000:
            warnings.append(f"LOW SALES: ₹{total_sales:,.0f} (full day, expect ₹5L+)")
    else:
        if total_inv < 200:
            warnings.append(f"LOW TOTAL: {total_inv} invoices (partial, expect 400+)")
        if total_sales < 100_000:
            warnings.append(f"LOW SALES: ₹{total_sales:,.0f} (partial, expect ₹2L+)")

    ratio = len(addon_records) / total_inv if total_inv else 0
    if ratio < 0.1:
        warnings.append(f"LOW ADDON RATIO: {ratio:.0%}")
    if ratio > 1.0:
        warnings.append(f"HIGH ADDON RATIO: {ratio:.0%}")

    # Hard stop only on a real export failure.
    fatal = len(outlet) < 5 or total_inv < 50
    return warnings, fatal


# ---------------------------------------------------------------------------
# Step 2 (+2.8): export, with double-export and morning reconciliation
# ---------------------------------------------------------------------------
def export_and_dedupe(pp: Petpooja, target_date: str, run_mode: str,
                      headless: bool) -> tuple[list[dict], dict]:
    from browser_export import export_order_csv
    meta: dict = {}

    csv1 = export_order_csv(target_date, OUTPUTS, tag="1", headless=headless)
    n1 = sum(1 for _ in open(csv1, encoding="utf-8-sig")) - 1
    log(f"  export #1: {csv1.name} ({n1} rows)")
    lag = int(os.environ.get("NBDD_EXPORT_SLEEP", "180"))  # sync-lag window (override for dry runs)
    log(f"  waiting {lag}s for late-syncing orders before re-export ...")
    time.sleep(lag)  # blocking is fine in a plain script
    csv2 = export_order_csv(target_date, OUTPUTS, tag="2", headless=headless)
    n2 = sum(1 for _ in open(csv2, encoding="utf-8-sig")) - 1
    log(f"  export #2: {csv2.name} ({n2} rows)")
    chosen = csv2 if n2 >= n1 else csv1
    meta.update(export_rows=(n1, n2), export_used=chosen.name)

    records = dedupe_csv(chosen, target_date, run_mode)
    export_total = sum(r["totalSales"] for r in records if r["status"] == "Success")

    # Step 2.8 — morning only: reconcile vs POS dashboard, re-export if short.
    if run_mode == "morning":
        try:
            pos = pp.pos_dashboard_total()
        except Exception as e:  # noqa: BLE001
            meta["reconcile"] = f"pos read failed: {e}"
            return records, meta
        pos_total = pos.get("total")
        meta["pos_total"] = pos_total
        meta["export_total_before"] = export_total
        if pos_total and export_total < pos_total - RECONCILE_THRESHOLD:
            decision = "reexport"
            j = claude_assist.reconcile_judgment({
                "pos_total": pos_total, "export_total": export_total,
                "delta": export_total - pos_total, "threshold": RECONCILE_THRESHOLD,
                "already_reexported": False,
            })
            if j.ok:
                decision = j.value
                meta["reconcile_note"] = j.note
            if decision == "reexport":
                csv3 = export_order_csv(target_date, OUTPUTS, tag="3", headless=headless)
                rec3 = dedupe_csv(csv3, target_date, run_mode)
                t3 = sum(r["totalSales"] for r in rec3 if r["status"] == "Success")
                # keep whichever is closer to POS
                if abs(t3 - pos_total) < abs(export_total - pos_total):
                    records, export_total = rec3, t3
                    meta["export_used"] = csv3.name
                meta["reconcile"] = f"re-exported; export_total now ₹{export_total:,.0f}"
            else:
                meta["reconcile"] = "accepted without re-export"
        else:
            meta["reconcile"] = "within threshold" if pos_total else "no POS total read"
    return records, meta


# ---------------------------------------------------------------------------
# selftest / dry-run / live
# ---------------------------------------------------------------------------
def do_selftest() -> int:
    log("SELFTEST — proves the moving parts without writing anything.\n")
    ok = True

    # 1) dashboard marker integrity
    try:
        dash = newest_dashboard()
        data = dash.read_bytes()[:0]  # touch
        with open(dash, "rb") as f:
            head = f.read(9_000_000)
        i = head.find(db.MARKER)
        assert i != -1 and head[i + db.MARKER_LEN:i + db.MARKER_LEN + 1] == b"[", "marker/offset bad"
        log(f"  [OK  ] dashboard marker parses  ({dash.name})")
    except Exception as e:  # noqa: BLE001
        ok = False
        log(f"  [FAIL] dashboard marker: {e}")

    # 2) Petpooja session alive (cheap HTTP GET, not the login page)
    try:
        pp = Petpooja.from_tokens()
        pp._get("/users/dashboard")  # raises SessionExpired if bounced to login
        log("  [OK  ] Petpooja session alive (HTTP)")
    except SessionExpired as e:
        ok = False
        log(f"  [FAIL] session: {e}")
    except Exception as e:  # noqa: BLE001
        ok = False
        log(f"  [FAIL] session check: {e}")

    # 3) Playwright addon scrape for one outlet, verified against its Total row
    try:
        from browser_export import scrape_addons
        d = config.SELFTEST["business_date"]
        oid = 349767
        out = scrape_addons(d, [oid], headless=True)
        if out["errors"].get(oid):
            ok = False
            log(f"  [FAIL] addon scrape {config.SHORT[oid]} {d}: {out['errors'][oid]}")
        else:
            rows = out["results"].get(oid, [])
            log(f"  [OK  ] addons {config.SHORT[oid]} {d}: {len(rows)} rows, sums verified")
    except Exception as e:  # noqa: BLE001
        ok = False
        log(f"  [FAIL] addon scrape: {e}")

    log(f"\nClaude assist: {'ARMED' if claude_assist.available() else 'dormant (no key)'}")
    log("\nClient is healthy." if ok else "\nSELFTEST FAILED — do not trust writes.")
    return 0 if ok else 1


def run(dry_run: bool, target_date: str, run_mode: str, headless: bool) -> int:
    OUTPUTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    now = datetime.now(IST)
    log(f"Now IST: {now}")
    log(f"Run mode: {run_mode} | target_date: {target_date} | {'DRY-RUN' if dry_run else 'LIVE'}\n")

    pp = Petpooja.from_tokens()

    log("Step 2: export CSV (Playwright) + dedupe ...")
    records, meta = export_and_dedupe(pp, target_date, run_mode, headless)
    log(f"  deduped invoices: {len(records)}")
    for k, v in meta.items():
        log(f"  {k}: {v}")

    log("\nStep 4: addons (Playwright, report 31 is JS-rendered) ...")
    addon_records, addon_warns = pull_addons(target_date, headless=headless)
    log(f"  addon records: {len(addon_records)} across outlets")

    log("\nStep 4B: validation ...")
    warnings, fatal = validate(records, addon_records, run_mode)
    warnings += addon_warns
    for w in warnings:
        log(f"  ⚠️  {w}")
    if not warnings:
        log("  ✅ all checks passed")
    if fatal:
        log("\nFATAL: export looks broken (<5 outlets or <50 invoices). Not writing.")
        return 2

    total_sales = sum(r["totalSales"] for r in records if r["status"] == "Success")
    log(f"\n  target_date Success sales (export): ₹{total_sales:,.0f}")
    log(f"  total quantity rows: {len(records)}  | addon rows: {len(addon_records)}")

    log("\nStep 5: rebuild DAILY_DATA ...")
    dash = newest_dashboard()
    workdir = Path("/tmp/nbdd") if os.name != "nt" else (OUTPUTS / "build")
    res = db.rebuild(dash, target_date, records, addon_records, run_mode, workdir)
    log(f"  kept {res.kept_records} | dropped {res.dropped_records} | appended {res.appended_records}")
    log(f"  prev-day biz sales before/after: ₹{res.prev_biz_before:,.0f} / ₹{res.prev_biz_after:,.0f} "
        f"({'STABLE' if res.prev_stable else 'CHANGED!'})")
    log(f"  new file: {res.new_html} (md5 {res.md5})")
    for w in res.warnings:
        log(f"  ⚠️  {w}")

    if not res.prev_stable:
        log("\nABORT: prev-day sales changed — the drop step over-deleted. Not writing.")
        return 3

    # Optional Claude anomaly note (dormant without a key).
    if warnings and claude_assist.available():
        note = claude_assist.explain_anomaly({
            "run_mode": run_mode, "target_date": target_date,
            "total_sales": total_sales, "invoices": len(records),
            "warnings": warnings,
        })
        if note.ok:
            log(f"\n  🧠 claude note: {note.value}")

    if dry_run:
        log("\nDRY-RUN complete — nothing written to the dashboard or Supabase.")
        return 0

    # LIVE: write to the mount once, then publish.
    log("\nWriting updated dashboard to disk ...")
    import shutil
    shutil.copyfile(res.new_html, dash)
    log(f"  wrote {dash}")

    log("Step 7: publish to Supabase ...")
    env = db.read_env_local(config.ENV_LOCAL)
    pub = db.publish(res.new_html, env["NEXT_PUBLIC_SUPABASE_URL"],
                     env["SUPABASE_SERVICE_ROLE_KEY"])
    if pub.get("ok"):
        log(f"  🌐 website updated (hash verified) — http {pub['http']}, gz {pub['gz_size']//1024} KB")
    else:
        log(f"  ⚠️  publish issue: {pub}")
        log("  The 09:35 / 16:40 check-in tasks will catch and fix it.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date", help="override target date YYYY-MM-DD")
    ap.add_argument("--mode", choices=["morning", "afternoon"], help="override run mode")
    ap.add_argument("--headed", action="store_true", help="show the export browser")
    args = ap.parse_args()

    if args.selftest:
        return do_selftest()

    now = datetime.now(IST)
    tgt, mode = compute_target(now)
    if args.date:
        tgt = args.date
    if args.mode:
        mode = args.mode
    try:
        return run(args.dry_run, tgt, mode, headless=not args.headed)
    except SessionExpired as e:
        log(f"\nSESSION EXPIRED: {e}")
        return 1
    except Exception:  # noqa: BLE001
        log("\nUNHANDLED ERROR:\n" + traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
