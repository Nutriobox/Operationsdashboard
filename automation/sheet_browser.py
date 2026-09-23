"""
Google Sheets reader — API edition (2026-09-23).

Same class/func names as before (BrowserReader, login, SessionExpired) so callers
are unchanged. Reads via the Sheets API as the robot service account
(sheets_api.py) — no signed-in browser, nothing to log out.

Exact tab-name matching is kept: rows() refuses a tab that doesn't exist
(the old gviz endpoint silently returned a DIFFERENT tab on a bad name).

Fallback: env NUTRIO_SHEETS_MODE=ui, or an .xlsx workbook, uses the old browser
reader (sheet_browser_ui.py).
"""
from __future__ import annotations

import os

import sheets_api
from sheets_api import ApiAccessError, OfficeFileError


class SessionExpired(RuntimeError):
    """Robot account can't read the sheet (kept name for callers)."""


class BrowserReader:
    def __init__(self, headless: bool = True, timeout_ms: int = 45000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._api = None
        self._ui = None

    def __enter__(self):
        if os.environ.get("NUTRIO_SHEETS_MODE", "").lower() == "ui":
            self._start_ui()
        else:
            self._api = sheets_api.SheetsApi()
        return self

    def __exit__(self, *exc):
        if self._ui is not None:
            self._ui.__exit__(*exc)

    def _start_ui(self):
        import sheet_browser_ui
        self._ui = sheet_browser_ui.BrowserReader(headless=self.headless,
                                                  timeout_ms=self.timeout_ms)
        self._ui.__enter__()

    def _call(self, fn_api, fn_ui):
        if self._ui is not None:
            return fn_ui()
        try:
            return fn_api()
        except OfficeFileError:
            self._start_ui()
            return fn_ui()
        except ApiAccessError as e:
            raise SessionExpired(str(e)) from e

    def tab_titles(self, sheet_id: str) -> list[str]:
        titles = self._call(lambda: self._api.titles(sheet_id),
                            lambda: self._ui.tab_titles(sheet_id))
        if not titles:
            raise SessionExpired("Read zero tabs from the sheet.")
        return titles

    def rows(self, sheet_id: str, tab: str) -> list[list[str]]:
        def api():
            if tab not in self._api.titles(sheet_id):
                raise SessionExpired(f"no tab named exactly {tab!r} in {sheet_id}")
            return self._api.grid(sheet_id, tab)
        return self._call(api, lambda: self._ui.rows(sheet_id, tab))


def login(sheet_id: str | None = None):
    """No longer needed for Sheets — kept so old .bat files don't crash."""
    print("\n  Google Sheets now use the robot account "
          f"({sheets_api.BOT_EMAIL}); no Google login is needed.")
    print("  If a job says it can't open a sheet, share that sheet with the "
          "robot email as Editor.\n")
    if os.environ.get("NUTRIO_SHEETS_MODE", "").lower() == "ui":
        import sheet_browser_ui
        sheet_browser_ui.login(sheet_id)
