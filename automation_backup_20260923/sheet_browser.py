"""
Playwright reader for Google Sheets — same persistent profile the rest of the
system uses (secrets/browser-profile, maintained by refresh_tokens.py).

Why a browser at all, when Sheets has an API: no service-account key to create,
rotate or keep off GitHub. The cost is that the profile must stay signed in to a
Google account that can see the sheet.

  from sheet_browser import BrowserReader
  with BrowserReader() as r:
      titles = r.tab_titles(SHEET_ID)      # read off the DOM
      rows   = r.rows(SHEET_ID, "Aug 10 - Aug 16, 2026")

THE FALLBACK HAZARD (this is the whole reason tab_titles() exists):
`gviz/tq?sheet=<name>` does NOT 404 on a name that doesn't exist — it silently
returns a DIFFERENT sheet. So we always read the real tab list from the DOM and
require an exact match before fetching. Never fuzzy-match, never "closest".
"""
from __future__ import annotations

import csv
import io
import time

import config

PROFILE_DIR = config.SECRETS / "browser-profile"
EDIT_URL = "https://docs.google.com/spreadsheets/d/{sid}/edit"
GVIZ_URL = ("https://docs.google.com/spreadsheets/d/{sid}/gviz/tq"
            "?tqx=out:csv&sheet={tab}&headers=0")


class SessionExpired(RuntimeError):
    """The profile is not signed in to Google."""


_TAB_JS = """() => Array.from(
    document.querySelectorAll('.docs-sheet-tab .docs-sheet-tab-name')
).map(e => e.textContent.trim())"""


class BrowserReader:
    def __init__(self, headless: bool = True, timeout_ms: int = 45000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = self._ctx = self._page = None
        self._opened: set[str] = set()

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        try:
            self._ctx = self._pw.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
        except Exception as e:
            self._pw.stop()
            if "ProcessSingleton" in str(e) or "SingletonLock" in str(e):
                raise SessionExpired(
                    "The browser profile is locked — another job (refresh_tokens.py, "
                    "daily_data.py) is using it right now, or a crashed run left a "
                    "lock behind. Wait for it to finish and retry."
                ) from e
            raise
        self._page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        self._page.set_default_timeout(self.timeout_ms)
        return self

    def __exit__(self, *exc):
        try:
            if self._ctx:
                self._ctx.close()
        finally:
            if self._pw:
                self._pw.stop()

    # -- internals ---------------------------------------------------------
    def _open(self, sheet_id: str):
        """Land on the sheet once per run so the context holds fresh cookies."""
        if sheet_id in self._opened:
            return
        page = self._page
        page.goto(EDIT_URL.format(sid=sheet_id), wait_until="domcontentloaded")
        for _ in range(3):
            if "accounts.google.com" in page.url or "/ServiceLogin" in page.url:
                raise SessionExpired(
                    "The browser profile is not signed in to Google.\n"
                    "  Fix: run  DELAY-LOGIN.bat  (opens a real window; sign in to the\n"
                    "  Google account that can see the Weekly Sales sheet, then close it)."
                )
            try:
                page.wait_for_selector(".docs-sheet-tab", timeout=self.timeout_ms // 3)
                break
            except Exception:
                page.wait_for_timeout(2000)
        else:
            raise SessionExpired(
                f"Sheet {sheet_id} never rendered its tab strip. Either the profile "
                f"lacks access to it, or the page is still loading. Current URL: {page.url}"
            )
        # The tab strip renders progressively on big workbooks.
        prev, stable = -1, 0
        for _ in range(15):
            n = len(self._page.evaluate(_TAB_JS))
            stable = stable + 1 if n == prev else 0
            if stable >= 2 and n > 0:
                break
            prev = n
            page.wait_for_timeout(500)
        self._opened.add(sheet_id)

    # -- public API (mirrors the shape of sheets.Sheets) --------------------
    def tab_titles(self, sheet_id: str) -> list[str]:
        """Visual order, leftmost first — read from the DOM, not from gviz."""
        self._open(sheet_id)
        titles = self._page.evaluate(_TAB_JS)
        if not titles:
            raise SessionExpired(
                "Read zero tabs from the sheet — the page did not finish rendering.")
        return titles

    def rows(self, sheet_id: str, tab: str) -> list[list[str]]:
        """
        The tab's cells as a list of rows. Fetched through the browser's own
        request context so the cookies and headers match a real click.
        """
        self._open(sheet_id)
        from urllib.parse import quote
        url = GVIZ_URL.format(sid=sheet_id, tab=quote(tab, safe=""))
        resp = self._ctx.request.get(url, timeout=self.timeout_ms)
        if resp.status != 200:
            raise SessionExpired(
                f"gviz returned HTTP {resp.status} for tab {tab!r}. "
                "The profile may have lost access to this sheet.")
        body = resp.text()
        if body.lstrip().startswith("<"):
            raise SessionExpired(
                "gviz returned HTML instead of CSV — that is the Google sign-in "
                "page. Run DELAY-LOGIN.bat.")
        return [r for r in csv.reader(io.StringIO(body))]


def login(sheet_id: str | None = None):
    """Open a real window so the user can sign in to Google once."""
    from playwright.sync_api import sync_playwright
    url = EDIT_URL.format(sid=sheet_id) if sheet_id else "https://accounts.google.com"
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=False,
            args=["--disable-blink-features=AutomationControlled"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url)
        print("\n  A browser window is open.")
        print("  Sign in to the Google account that can see the Weekly Sales sheet.")
        print("  When the spreadsheet is visible, come back here and press Enter.\n")
        try:
            input("  Press Enter when done... ")
        except EOFError:
            time.sleep(120)
        try:
            ctx.close()
        except Exception:
            # The window may already be closed (e.g. the user closed it manually
            # before pressing Enter). This is a persistent context, so the Google
            # session is already saved to the profile on disk — this cleanup
            # error is harmless and must not mask a successful sign-in.
            pass
    print("  Saved. The profile should stay signed in for weeks.")
