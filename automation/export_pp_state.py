"""
One-off: export the logged-in Petpooja browser session as an OS-independent
storage_state JSON (decrypted cookies + localStorage), so the AWS browser Lambda
can restore the SAME session the laptop profile holds.

Run on the laptop (the profile lives here and only Windows can decrypt it):
    python export_pp_state.py

Writes:  secrets\pp_storage_state.json   (upload target for AWS)
Prints:  LOGGED_IN / LOGGED_OUT so we know the capture is valid.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PROFILE = ROOT / "secrets" / "browser-profile"
OUT = ROOT / "secrets" / "pp_storage_state.json"
DASH = "https://billing.petpooja.com/users/dashboard"
LOGIN_MARKERS = ("UserLoginForm", "data[User][password]", "/users/login")

from playwright.sync_api import sync_playwright

def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), headless=True,
            args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(DASH, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(3000)
            html = page.content()
            logged_out = any(m in html for m in LOGIN_MARKERS)
            # Prime a single outlet + open KOT so any outlet-mode localStorage the
            # SPA writes is captured in the state too (best-effort).
            try:
                ctx.request.post("https://billing.petpooja.com/",
                                 form={"header_changed_rest_id": "159181"})
                page.goto(DASH, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(2500)
                try:
                    page.wait_for_selector('a[href*="kot_list"]', timeout=15_000)
                    page.click('a[href*="kot_list"]', timeout=8000)
                    page.wait_for_timeout(2500)
                except Exception:
                    pass
            except Exception:
                pass
            ctx.storage_state(path=str(OUT))
        finally:
            ctx.close()
    print("state written:", OUT)
    print("session:", "LOGGED_OUT (RE-LOGIN FIRST: refresh_tokens.py --login)" if logged_out else "LOGGED_IN")
    return 1 if logged_out else 0

if __name__ == "__main__":
    sys.exit(main())
