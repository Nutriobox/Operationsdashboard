"""
failure_watch.py  —  unattended failure alerting for the Nutriobox jobs.

Read-only. It never touches the pipeline: it just scans automation/logs/*.log
for the LAST run of each job, and if that run failed (its "==== EXIT n ===="
marker is non-zero) OR a scraper session is logged out, it emails Satvik ONE
concise message naming the job, the error, and the exact one-line fix.

De-duped via logs/.failure_watch_state.json — it only emails when a job's
latest failing run is NEW since the last alert (and clears state when a job
recovers), so you get told once per incident, not every run.

Reuses the Gmail sender already used by session_watch.py, so no new
credentials. Intended to run a few times a day via Windows Task Scheduler
(see FAILURE-WATCH-SCHEDULE.bat).

    python failure_watch.py            # scan, email new failures
    python failure_watch.py --dry-run  # scan + print, never email/update state
    python failure_watch.py --test     # send a test email and exit
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta

import config

# Reuse the exact env loader + Gmail sender session_watch already uses.
try:
    from session_watch import load_env, send_alert, ALERT_TO
except Exception as e:  # pragma: no cover - keep the watchdog alive regardless
    print(f"failure_watch: could not import session_watch ({e})")
    raise

IST = timezone(timedelta(hours=5, minutes=30))
STATE_FILE = config.LOGS / ".failure_watch_state.json"
EXIT_RE = re.compile(r"====\s*EXIT\s+(-?\d+)\s*====")
RUN_RE = re.compile(r"====.*RUN\s+(.+?)\s*====", re.IGNORECASE)

# (display name, log filename, the run_*.bat to re-run it by hand)
# A missing log file is simply skipped (scan_log -> None), so listing a job that
# has not produced a log yet is harmless — it starts being watched the moment it
# first runs. The month-boundary jobs were added 25 Sep 2026: incentive_delay and
# daily_sheet had been failing for weeks on missing month tabs with nothing
# watching them.
JOBS = [
    ("Sales - daily sheet fill",   "daily_sheet.log",        "run_daily_sheet.bat"),
    ("Sales - weekly fill",        "weekly_sales.log",       "run_weekly_sales.bat"),
    ("Sales - monthly fill",       "monthly_sales_fill.log", "run_monthly_sales_fill.bat"),
    ("Sales dashboard pull",       "daily_data.log",         "run_daily.bat"),
    ("Sales - monthly resync",     "monthly_resync.log",     "run_monthly_resync.bat"),
    ("Monthly dashboard",          "monthly_dashboard.log",  "run_monthly_dashboard.bat"),
    ("KOT - daily",                "kot_daily.log",          "run_kot_daily.bat"),
    ("KOT - weekly",               "kot_weekly.log",         "run_kot_weekly.bat"),
    ("KOT - monthly",              "kot_monthly.log",        "run_kot_monthly.bat"),
    ("Incentive - delay (weekly)", "incentive_delay.log",    "run_incentive_delay.bat"),
    ("Incentive - weekly",         "incentive_weekly.log",   "run_incentive_weekly.bat"),
    ("Incentive - monthly",        "incentive_monthly.log",  "run_incentive_monthly.bat"),
    ("Weekly report",              "weekly_report.log",      "run_weekly_report.bat"),
    ("Ratings",                    "ratings.log",            "run_ratings.bat"),
    ("Delay dashboard",            "delay.log",              "run_delay.bat"),
    ("Momos",                      "momos.log",              "run_momos.bat"),
    ("Discount (weekly)",          "discount.log",           "run_discount_weekly.bat"),
]


def fix_hint(tail: str, rerun_bat: str) -> str:
    """Map a known error signature in the log tail to a one-line fix."""
    t = tail.lower()
    if "not signed in to google" in t or "accounts.google.com" in t or "/servicelogin" in t:
        return ("Automation browser is logged out of GOOGLE. "
                "Fix: run DELAY-LOGIN.bat, sign in to Google, then press Enter in "
                "the black window (leave the browser open) — then re-run " + rerun_bat)
    if "session expired" in t or "petpooja logged out" in t or "petpooja.sessionexpired" in t:
        return ("Petpooja session logged out. "
                "Fix: run TOKENS-LOGIN.bat (or refresh_tokens.py --login), then re-run " + rerun_bat)
    if "s3 download failed http 403" in t or "http 403" in t:
        return ("Petpooja report export returned 403 (session/permission, usually "
                "the Petpooja cookie expiring). Fix: run TOKENS-LOGIN.bat, then re-run " + rerun_bat)
    if "err_connection_reset" in t or "net::err" in t or "timeout" in t or "err_timed_out" in t:
        return ("Transient network/Google error opening the sheet. Usually self-recovers; "
                "if data is missing just re-run " + rerun_bat)
    if "unicodeencodeerror" in t:
        return ("Console encoding crash. Fix: ensure the run_*.bat sets "
                "PYTHONIOENCODING=utf-8 (already patched for discount).")
    # Month-boundary signatures FIRST — they can co-occur with "verify failed"
    # in the same tail, and the month-tab remedy is more specific/useful.
    if ("not been extended for this month" in t or "carries the label" in t
            or "no row in column a" in t):
        return ("New month not seeded: the day-of-week tab has no column-A date row "
                "for this date yet (the daily fill deliberately refuses to append "
                "blindly). Add this month's date labels to column A of the affected "
                "weekday tab in the Sales Data sheet, then re-run " + rerun_bat)
    if ("does not exist" in t and "monthly run creates it" in t) or "refusing to create here" in t:
        return ("New month tab missing: the monthly run that creates this month's "
                "scored tab has not run yet. Fix: run run_incentive_monthly.bat "
                "(creates the month tab), then re-run " + rerun_bat)
    if "verify failed" in t:
        return ("Sheet read-back verification failed. Check the target tab/row, then re-run " + rerun_bat)
    if "already contain data" in t or "already filled" in t:
        return ("That date was already written (safe guard against double-write). "
                "No action unless the row is actually wrong.")
    return f"Check logs/{rerun_bat.replace('run_', '').replace('.bat', '.log')} for the traceback, then re-run {rerun_bat}"


def scan_log(path) -> dict | None:
    """Return {exit, run, tail} for the LAST run in a log, or None if unreadable."""
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None
    except Exception as e:
        return {"exit": None, "run": "?", "tail": f"(could not read log: {e})"}
    exits = list(EXIT_RE.finditer(data))
    if not exits:
        return None  # no completed run recorded in this format
    last = exits[-1]
    code = int(last.group(1))
    # the run header is the nearest "RUN ..." line before this EXIT
    head = data[:last.start()]
    runs = list(RUN_RE.finditer(head))
    run_label = runs[-1].group(1).strip() if runs else "?"
    # tail = text of just this last run (from its header to the exit)
    start = runs[-1].start() if runs else max(0, last.start() - 4000)
    tail = data[start:last.end()]
    return {"exit": code, "run": run_label, "tail": tail}


def session_failures(env: dict) -> list[dict]:
    """Report any scraper site that is logged out, from tokens.json."""
    out = []
    try:
        tok = json.loads(config.TOKENS_FILE.read_text(encoding="utf-8"))
        status = tok.get("status", {})
        bad = [s for s, v in status.items()
               if str(v).lower() != "ok" and not str(v).lower().startswith("unreachable")]
        if bad:
            out.append({
                "job": "Scraper session (" + ", ".join(bad) + ")",
                "sig": "session:" + ",".join(sorted(bad)),
                "detail": "Logged out: " + ", ".join(bad),
                "fix": "Run TOKENS-LOGIN.bat (refresh_tokens.py --login) to sign back in.",
            })
    except Exception:
        pass
    return out


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"failure_watch: could not write state ({e})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="scan + print, do not email or update state")
    ap.add_argument("--test", action="store_true", help="send a test email and exit")
    args = ap.parse_args()

    env = load_env()

    if args.test:
        ok = send_alert(env, "[Nutriobox] failure_watch test",
                        "This is a test alert from failure_watch.py. If you got this, "
                        "unattended failure alerting works.")
        print("test email sent" if ok else "test email FAILED (check Gmail creds in .env.local)")
        return 0 if ok else 1

    state = load_state()
    new_state = dict(state)
    failures = []

    # 1) job logs
    for display, fname, rerun_bat in JOBS:
        info = scan_log(config.LOGS / fname)
        if not info:
            continue
        key = fname
        if info["exit"] not in (0, None):
            sig = f"{info['run']}|EXIT {info['exit']}"
            new_state[key] = sig
            if state.get(key) != sig:  # new incident
                failures.append({
                    "job": display,
                    "sig": sig,
                    "detail": f"last run {info['run']} exited {info['exit']}",
                    "fix": fix_hint(info["tail"], rerun_bat),
                })
        else:
            new_state.pop(key, None)  # recovered -> allow future re-alert

    # 2) scraper sessions
    for f in session_failures(env):
        key = f["sig"]
        new_state[key] = "1"
        if key not in state:
            failures.append(f)
        # note: session recovery is reflected by absence next scan

    # prune recovered session keys from state
    live_session_keys = {f["sig"] for f in session_failures(env)}
    for k in list(new_state):
        if k.startswith("session:") and k not in live_session_keys:
            new_state.pop(k, None)

    now = datetime.now(IST).strftime("%d %b %Y %H:%M IST")
    if not failures:
        print(f"[{now}] failure_watch: all clear, no new failures.")
        if not args.dry_run:
            save_state(new_state)
        return 0

    lines = [f"Nutriobox automation — {len(failures)} issue(s) need attention",
             f"Checked {now}", ""]
    for f in failures:
        lines.append(f"* {f['job']}")
        lines.append(f"    {f['detail']}")
        lines.append(f"    FIX: {f['fix']}")
        lines.append("")
    body = "\n".join(lines)
    print(body)

    if args.dry_run:
        print("(dry-run: no email sent, state unchanged)")
        return 0

    subject = f"[Nutriobox] {len(failures)} automation job(s) failing"
    sent = send_alert(env, subject, body)
    print("alert emailed" if sent else "ALERT SEND FAILED")
    save_state(new_state)  # save even if email failed, to avoid a loop; recovery re-alerts
    return 0


if __name__ == "__main__":
    sys.exit(main())
