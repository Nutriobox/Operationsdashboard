"""
Session watchdog — keeps the automation logins alive, and makes it impossible
for them to die quietly.

Background (27 Aug 2026): the shared browser profile signed out of Petpooja,
Zomato and Swiggy. `daily_data.py` failed six consecutive runs over six days and
nobody noticed, because the legacy Claude tasks silently covered the same work.
The renewal machinery was fine — `refresh_tokens.py` already runs headless twice
a day. What was missing was a voice.

This script adds three things:

  1. EARLY WARNING — reads the real cookie expiry times out of the browser
     profile and warns while the session is still healthy (default: 3 days
     ahead), so the fix lands during working hours instead of at 04:00.
  2. ALERTING — emails satvik@ the moment a site degrades, using the Gmail
     credentials already in .env.local.
  3. A PUBLISHED STATUS FILE — uploads reports/session-status.json to Supabase
     so the daily health check (and the dashboard) can see per-site state
     without reading laptop logs.

    python session_watch.py                 REM check + publish + alert if degraded
    python session_watch.py --check         REM print status only, no email, no upload
    python session_watch.py --alert-test    REM send a test email and exit

Exit codes:  0 healthy · 1 warning (expiring soon) · 2 degraded (a site is out)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path

import config

IST = timezone(timedelta(hours=5, minutes=30))
PROFILE_DIR = config.SECRETS / "browser-profile"
TOKENS = config.TOKENS_FILE
STATUS_OBJECT = "reports/session-status.json"

WARN_DAYS = 3
ALERT_TO = "satvik@nutriobox.com"

SITE_DOMAINS = {
    "petpooja": "petpooja.com",
    "zomato": "zomato.com",
    "swiggy": "swiggy.com",
}

# Google Sheets writing profile. This is a SEPARATE session from the
# Petpooja/Zomato/Swiggy tokens above: it is the signed-in Google account
# (mayank@nutriobox.com) in the persistent browser profile that kot_daily.py,
# weekly_sales_sync.py, daily_sheet.py and delay_dashboard.py write through.
# It logged out on 25 Sep 2026 and nothing was watching it — kot_daily and
# weekly_sales failed silently. We now probe it every run: a gviz CSV export of
# a PRIVATE sheet returns CSV when signed in, or the sign-in HTML when not
# (same signal sheet_writer_ui.py already relies on). Fix on logout:
# run DELAY-LOGIN.bat and sign in as mayank@nutriobox.com.
GOOGLE_PROBE_SHEET = "1yOYpZBjohebpfpjRIfrDnUNd21bDcFcbt2vem1D_mn8"  # Daily KOT (private)
GVIZ_URL = ("https://docs.google.com/spreadsheets/d/{sid}/gviz/tq"
            "?tqx=out:csv&headers=0&_cb={cb}")


# ---------------------------------------------------------------------------
# env
# ---------------------------------------------------------------------------
def load_env() -> dict:
    """Read .env.local without printing anything from it."""
    env: dict[str, str] = {}
    if config.ENV_LOCAL.exists():
        for line in config.ENV_LOCAL.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip().lstrip("\ufeff")
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
              "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


# ---------------------------------------------------------------------------
# cookie expiry lookahead
# ---------------------------------------------------------------------------
def cookie_expiry() -> dict[str, str | None]:
    """
    Soonest meaningful cookie expiry per site, read from the live profile.

    This is the early-warning signal: it tells us a session is *going* to die
    before it actually does. Session cookies (no expiry) are ignored — they die
    with the browser, not on a clock.
    """
    out: dict[str, str | None] = {k: None for k in SITE_DOMAINS}
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return out

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            soonest: dict[str, float] = {}
            for c in ctx.cookies():
                exp = c.get("expires")
                if not exp or exp <= 0:
                    continue
                dom = c.get("domain", "") or ""
                for site, needle in SITE_DOMAINS.items():
                    if needle in dom:
                        # Ignore long-lived marketing cookies: we care about the
                        # earliest credential-ish cookie, but not ones already
                        # expired.
                        now = datetime.now(timezone.utc).timestamp()
                        if exp > now and (site not in soonest or exp < soonest[site]):
                            soonest[site] = exp
            for site, ts in soonest.items():
                out[site] = datetime.fromtimestamp(ts, IST).isoformat()
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    return out


# ---------------------------------------------------------------------------
# google sheets writing profile
# ---------------------------------------------------------------------------
def google_status() -> str:
    """
    Liveness of the signed-in Google profile used for all Sheets writes.

    Returns one of:
      "ok"          — gviz returned CSV, the profile is signed in.
      "LOGGED OUT"  — gviz returned the sign-in page (or a redirect to it).
      "unknown: …"  — the probe itself could not run (playwright/network); we do
                      NOT treat this as a logout, to avoid false alarms.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return f"unknown: playwright unavailable ({e})"

    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR), headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                cb = int(datetime.now(timezone.utc).timestamp() * 1000)
                url = GVIZ_URL.format(sid=GOOGLE_PROBE_SHEET, cb=cb)
                resp = ctx.request.get(url, timeout=30000)
                if resp.status != 200:
                    # 302 to accounts.google.com is followed to a 200 HTML page,
                    # so a non-200 here is unusual; treat as inconclusive.
                    return f"unknown: gviz HTTP {resp.status}"
                body = resp.text()
                if body.lstrip().startswith("<") or "accounts.google.com" in body[:2000]:
                    return "LOGGED OUT"
                return "ok"
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass
    except Exception as e:
        msg = str(e).splitlines()[0] if str(e) else e.__class__.__name__
        if "SingletonLock" in str(e) or "ProcessSingleton" in str(e):
            return "unknown: profile locked (another job running)"
        return f"unknown: probe failed ({msg})"


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------
def read_status() -> dict:
    if not TOKENS.exists():
        return {"status": {}, "refreshed_at": None}
    try:
        d = json.loads(TOKENS.read_text(encoding="utf-8"))
    except Exception:
        return {"status": {}, "refreshed_at": None}
    return {"status": d.get("status", {}), "refreshed_at": d.get("refreshed_at")}


def classify(status: dict, expiry: dict, google: str = "unknown") -> tuple[str, list[str]]:
    """Return (level, messages). level = healthy | warning | degraded."""
    msgs: list[str] = []
    level = "healthy"

    for site in SITE_DOMAINS:
        state = str(status.get(site, "unknown"))
        if state.lower().startswith("unreachable"):
            # page didn't load (network / bot-check) — cookies are kept; not a logout
            msgs.append(f"{site}: page did not load this time (not a logout): {state[:80]}")
            continue
        if state.lower() != "ok":
            level = "degraded"
            msgs.append(f"{site}: LOGGED OUT ({state})")

    # Google Sheets writing profile (separate from the tokens above).
    g = str(google or "unknown")
    if g == "LOGGED OUT":
        level = "degraded"
        msgs.append("google (Sheets writing profile): LOGGED OUT — "
                    "kot_daily / weekly_sales / daily_sheet will all fail. "
                    "Fix: run DELAY-LOGIN.bat and sign in as mayank@nutriobox.com.")
    elif g.startswith("unknown"):
        # probe could not run — surface it but do not escalate the level
        msgs.append(f"google (Sheets writing profile): probe inconclusive ({g[8:].strip() or 'no detail'})")

    if level != "degraded":
        now = datetime.now(IST)
        for site, iso in expiry.items():
            if not iso:
                continue
            try:
                when = datetime.fromisoformat(iso)
            except ValueError:
                continue
            days = (when - now).total_seconds() / 86400
            if days <= WARN_DAYS:
                level = "warning"
                msgs.append(f"{site}: session cookie expires in {days:.1f} days "
                            f"({when:%d %b %H:%M})")
    return level, msgs


# ---------------------------------------------------------------------------
# alerting
# ---------------------------------------------------------------------------
def gmail_token(env: dict) -> str | None:
    need = ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")
    if not all(env.get(k) for k in need):
        return None
    data = urllib.parse.urlencode({
        "client_id": env["GMAIL_CLIENT_ID"],
        "client_secret": env["GMAIL_CLIENT_SECRET"],
        "refresh_token": env["GMAIL_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    try:
        with urllib.request.urlopen(
            urllib.request.Request("https://oauth2.googleapis.com/token", data=data),
            timeout=30,
        ) as r:
            return json.loads(r.read()).get("access_token")
    except Exception:
        return None


def send_alert(env: dict, subject: str, body: str) -> bool:
    tok = gmail_token(env)
    if not tok:
        print("  ! Gmail credentials unavailable — cannot send alert")
        return False
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = ALERT_TO
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode(),
        headers={"Authorization": f"Bearer {tok}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except Exception as e:
        print(f"  ! alert send failed: {e}")
        return False


def publish(env: dict, payload: dict) -> bool:
    url, key = env.get("NEXT_PUBLIC_SUPABASE_URL"), env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return False
    req = urllib.request.Request(
        f"{url}/storage/v1/object/{STATUS_OBJECT}",
        data=json.dumps(payload, indent=2).encode(),
        method="PUT",
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "Cache-Control": "no-cache, max-age=60", "x-upsert": "true"},
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status in (200, 201)
    except Exception as e:
        print(f"  ! publish failed: {e}")
        return False


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="print only")
    ap.add_argument("--alert-test", action="store_true")
    args = ap.parse_args()

    env = load_env()

    if args.alert_test:
        ok = send_alert(env, "NutrioBox automation — alert test",
                        "This is a test from session_watch.py. Alerting works.")
        print("alert test:", "sent" if ok else "FAILED")
        return 0 if ok else 2

    st = read_status()
    expiry = cookie_expiry()
    google = google_status()
    level, msgs = classify(st["status"], expiry, google)

    print(f"checked at   : {datetime.now(IST):%Y-%m-%d %H:%M} IST")
    print(f"refreshed_at : {st['refreshed_at']}")
    for site in SITE_DOMAINS:
        exp = expiry.get(site) or "—"
        print(f"  {site:9} {str(st['status'].get(site, 'unknown')):24} expires {exp}")
    print(f"  {'google':9} {google:24} (Sheets writing profile)")
    print(f"level        : {level.upper()}")
    for m in msgs:
        print(f"  - {m}")

    if args.check:
        return {"healthy": 0, "warning": 1, "degraded": 2}[level]

    payload = {
        "level": level,
        "sites": {**{s: str(st["status"].get(s, "unknown")) for s in SITE_DOMAINS},
                  "google": google},
        "expiry": expiry,
        "messages": msgs,
        "refreshed_at": st["refreshed_at"],
        "checkedAt": datetime.now(IST).isoformat(),
    }
    print("publish      :", "ok" if publish(env, payload) else "failed")

    if level != "healthy":
        subject = ("NutrioBox automation — SESSION LOGGED OUT"
                   if level == "degraded"
                   else "NutrioBox automation — session expiring soon")
        # The two logins are different accounts / different helpers, so spell out
        # both and let the reader pick the one that matches the messages above.
        google_out = google == "LOGGED OUT"
        sites_out = any(str(st["status"].get(s, "")).lower() not in ("ok", "")
                        and not str(st["status"].get(s, "")).lower().startswith("unreachable")
                        for s in SITE_DOMAINS)
        fix_lines = ["\n\nFix (about 3 minutes each, on the office laptop):"]
        if sites_out or not google_out:
            fix_lines.append(
                "  Petpooja / Zomato / Swiggy  ->  run TOKENS-LOGIN.bat\n"
                "    (or: cd C:\\Users\\hp\\Downloads\\Operationsdashboard\\automation\n"
                "         python refresh_tokens.py --login)")
        if google_out:
            fix_lines.append(
                "  Google Sheets writing profile  ->  run DELAY-LOGIN.bat\n"
                "    then sign in as mayank@nutriobox.com and close the window.")
        body = (
            f"Automation session status: {level.upper()}\n\n"
            + "\n".join(f"  - {m}" for m in msgs)
            + "\n".join(fix_lines)
            + "\n\nSign in to each item listed above when the browser opens.\n\n"
              "Jobs affected while this is unresolved: sales dashboard, KOT\n"
              "comparisons, daily sheet, weekly sales, momos weekly, offer tracker.\n"
        )
        print("alert        :", "sent" if send_alert(env, subject, body) else "failed")

    return {"healthy": 0, "warning": 1, "degraded": 2}[level]


if __name__ == "__main__":
    sys.exit(main())
