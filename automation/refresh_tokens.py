"""
Token broker — the ONLY browser left in the system.

Everything else (petpooja.py, the Swiggy/Zomato pulls, the Sheets writes) is
plain HTTP. This script exists purely to keep session credentials fresh.

  python refresh_tokens.py --login     one-time (and whenever a site logs out):
                                       opens a real browser, you sign in by hand
  python refresh_tokens.py             daily: headless, harvests tokens
  python refresh_tokens.py --check     just report what's alive/dead

Writes secrets/tokens.json:
  { "petpooja_cookie": "...", "zomato_cookie": "...", "swiggy_access_token": "...",
    "refreshed_at": "...", "status": {...} }

The browser profile lives in secrets/browser-profile/ and persists logins across
runs, so the headless pass normally just works for weeks at a time.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright

import config

IST = timezone(timedelta(hours=5, minutes=30))
PROFILE_DIR = config.SECRETS / "browser-profile"

SITES = {
    "petpooja": "https://billing.petpooja.com/users/dashboard",
    "zomato":   "https://www.zomato.com/partners/onlineordering/offers/trackOffers?resId=21529349",
    "swiggy":   "https://partner.swiggy.com/food/growth/discounts",
}


NETWORK_HINTS = ("ERR_HTTP2_PROTOCOL_ERROR", "chrome-error://", "ERR_CONNECTION",
                 "ERR_NETWORK", "ERR_TIMED_OUT", "ERR_NAME_NOT_RESOLVED",
                 "ERR_INTERNET_DISCONNECTED", "Timeout", "interrupted by another navigation")


def _visit(page, url: str, settle_ms: int) -> None:
    """goto with retries. Zomato/Swiggy often reject a single headless load with
    ERR_HTTP2_PROTOCOL_ERROR / a chrome-error redirect; that is a NETWORK/bot-check
    blip, not a logout (2026-09-23). Retry 3x with back-off before giving up."""
    last = None
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(settle_ms)
            if page.url.startswith("chrome-error://"):
                raise RuntimeError("landed on chrome-error:// page")
            return
        except Exception as e:
            last = e
            page.wait_for_timeout(5_000 * (attempt + 1))
    raise last


def _err_status(e: Exception) -> str:
    msg = str(e).splitlines()[0][:120]
    if any(h in str(e) for h in NETWORK_HINTS):
        return f"unreachable (network/bot-check, NOT a logout): {msg}"
    return f"error: {msg}"


def _cookie_header(context, url_substr: str) -> str:
    parts = [f"{c['name']}={c['value']}"
             for c in context.cookies()
             if url_substr in c.get("domain", "")]
    return "; ".join(parts)


def harvest(headless: bool = True) -> dict:
    config.SECRETS.mkdir(parents=True, exist_ok=True)
    out: dict = {"status": {}}

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # --- Petpooja -----------------------------------------------------
        try:
            _visit(page, SITES["petpooja"], 4_000)
            logged_in = page.locator("#selected_restaurant_id").count() > 0
            if logged_in:
                out["petpooja_cookie"] = _cookie_header(ctx, "petpooja.com")
                out["status"]["petpooja"] = "ok"
            else:
                out["status"]["petpooja"] = "LOGGED OUT — run --login"
        except Exception as e:
            out["status"]["petpooja"] = _err_status(e)

        # --- Zomato -------------------------------------------------------
        try:
            _visit(page, SITES["zomato"], 4_000)
            ck = _cookie_header(ctx, "zomato.com")
            if ck:
                out["zomato_cookie"] = ck
                out["status"]["zomato"] = "ok"
            else:
                out["status"]["zomato"] = "LOGGED OUT — run --login"
        except Exception as e:
            out["status"]["zomato"] = _err_status(e)

        # --- Swiggy (token lives in localStorage, not a cookie) ------------
        try:
            _visit(page, SITES["swiggy"], 6_000)
            token = page.evaluate("() => localStorage.getItem('access_token')")
            if token:
                out["swiggy_access_token"] = token
                out["swiggy_cookie"] = _cookie_header(ctx, "swiggy.com")
                out["status"]["swiggy"] = "ok"
            else:
                out["status"]["swiggy"] = "LOGGED OUT — run --login"
        except Exception as e:
            out["status"]["swiggy"] = _err_status(e)

        ctx.close()

    out["refreshed_at"] = datetime.now(IST).isoformat()
    return out


def login_flow():
    """Headed browser. Sign in to each site by hand, then press Enter."""
    config.SECRETS.mkdir(parents=True, exist_ok=True)
    print("Opening a browser. Sign in to each tab, then come back here.\n")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        for name, url in SITES.items():
            pg = ctx.new_page()
            pg.goto(url, wait_until="domcontentloaded")
            print(f"  - {name}: {url}")
        input("\nSign in to all three, then press Enter here... ")
        # If you closed the browser window yourself before pressing Enter, the
        # context is already gone and close() raises TargetClosedError. That
        # used to abort the whole run BEFORE harvest() — losing the sign-in you
        # just did. The profile is written to disk continuously, so a closed
        # window is harmless: swallow it and carry on to the harvest.
        try:
            ctx.close()
        except Exception as e:
            print(f"  (browser was already closed: {type(e).__name__} — continuing)")
    print("\nProfile saved. Harvesting tokens...\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", action="store_true",
                    help="headed browser for manual sign-in (one-time)")
    ap.add_argument("--check", action="store_true",
                    help="report token health without writing")
    args = ap.parse_args()

    if args.login:
        login_flow()

    tokens = harvest(headless=not args.login)

    print("Token status:")
    dead = []
    for site, st in tokens["status"].items():
        mark = "OK  " if st == "ok" else ("WARN" if st.startswith("unreachable") else "FAIL")
        print(f"  [{mark}] {site:9s} {st}")
        if st != "ok" and not st.startswith("unreachable"):
            dead.append(site)

    if args.check:
        return 1 if dead else 0

    # Merge, so a single dead site doesn't wipe the other two working tokens.
    existing = {}
    if config.TOKENS_FILE.exists():
        try:
            existing = json.loads(config.TOKENS_FILE.read_text())
        except json.JSONDecodeError:
            pass
    for k, v in tokens.items():
        if k == "status" or v:
            existing[k] = v
    existing["status"] = tokens["status"]

    config.TOKENS_FILE.write_text(json.dumps(existing, indent=2))
    print(f"\nWrote {config.TOKENS_FILE}")

    if dead:
        print(f"\n{len(dead)} site(s) need a manual sign-in:  python refresh_tokens.py --login")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
