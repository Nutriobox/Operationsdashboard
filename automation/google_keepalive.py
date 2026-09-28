"""
Keep the mayank@ GOOGLE session warm.

The scraper keepalive (refresh_tokens.py) only touches Petpooja/Zomato/Swiggy.
The Google login used to WRITE the .xlsx "Sales Data" (via the browser UI writer)
was never kept warm — so between the twice-daily jobs it sat idle and went stale,
which is a big part of why it kept logging out. This opens the same browser
profile headlessly every few hours and loads an authenticated Google page, which
refreshes the session cookies (same idea as the scraper keepalive).

  python google_keepalive.py            touch the session, print ok / LOGGED OUT

It only READS (loads a page) — it never writes. Safe to run on the 4-hourly
keepalive schedule. If it reports LOGGED OUT, session_watch's alert to mayank@
will already have fired; the fix is DELAY-LOGIN.bat.
"""
from __future__ import annotations
import sys
import config

PROFILE_DIR = config.SECRETS / "browser-profile"
# Light authenticated page — refreshes the Google session without loading the
# heavy ~big .xlsx. If we're signed in, this renders; if not, it redirects to
# accounts.google.com.
WARM_URL = "https://docs.google.com/spreadsheets/u/0/"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main() -> int:
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    ctx = None
    try:
        try:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=True,
                viewport={"width": 1600, "height": 1000},
                args=["--disable-blink-features=AutomationControlled",
                      "--window-size=1600,1000"],
            )
        except Exception as e:
            # Another job holds the profile — that's fine, the session is being
            # used (and thus kept warm) anyway. Not a failure.
            if "ProcessSingleton" in str(e) or "SingletonLock" in str(e):
                print("google keepalive: profile in use by another job — skipping (session is active)")
                return 0
            raise
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(45000)
        for attempt in range(3):
            try:
                page.goto(WARM_URL, wait_until="domcontentloaded", timeout=45000)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"google keepalive: navigation failed ({str(e).splitlines()[0][:80]})")
                    return 0  # transient network — not a login problem
                page.wait_for_timeout(2000 * (attempt + 1))
        page.wait_for_timeout(2500)
        if "accounts.google.com" in page.url or "/ServiceLogin" in page.url:
            print("google keepalive: LOGGED OUT — run DELAY-LOGIN.bat (sign in as mayank@nutriobox.com)")
            return 1
        print("google keepalive: ok — session refreshed")
        return 0
    finally:
        try:
            if ctx:
                ctx.close()
        finally:
            pw.stop()


if __name__ == "__main__":
    raise SystemExit(main())
