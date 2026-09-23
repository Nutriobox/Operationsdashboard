"""
Google Sheets over the official API, as the robot service account
(nutriobox-bot@nutriobox-ratings.iam.gserviceaccount.com, key in
secrets/nutriobox-sa.json).

WHY (2026-09-23): every Sheets job used to drive a *signed-in Chrome* as
mayank@. Google periodically kills sessions in automated browsers, and each
time it did, 7 jobs failed together (KOT daily/weekly/monthly, daily sheet,
delay, incentive, weekly/monthly sales) until someone ran DELAY-LOGIN.bat.
A service account has no browser session, so it cannot be "logged out".

Requirement: each sheet must be shared with the bot email as Editor, and must
be a native Google Sheet (NOT an uploaded .xlsx — the API refuses Office files).

Only depends on google-auth + requests (both already installed).
"""
from __future__ import annotations

import time
from urllib.parse import quote

import config

BOT_EMAIL = "nutriobox-bot@nutriobox-ratings.iam.gserviceaccount.com"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BASE = "https://sheets.googleapis.com/v4/spreadsheets"


class ApiAccessError(RuntimeError):
    """The bot cannot open this sheet (not shared, or it's an .xlsx)."""


class OfficeFileError(ApiAccessError):
    """The document is an uploaded Office (.xlsx) file — API can't touch it."""


def a1_range(tab: str, rng: str | None = None) -> str:
    t = "'" + tab.replace("'", "''") + "'"
    return f"{t}!{rng}" if rng else t


def col_to_num(letters: str) -> int:
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def num_to_col(n: int) -> str:
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def split_a1(a1: str) -> tuple[int, int]:
    """'B12' -> (col=2, row=12), both 1-based."""
    a1 = a1.strip().upper()
    i = 0
    while i < len(a1) and a1[i].isalpha():
        i += 1
    return col_to_num(a1[:i]), int(a1[i:])


class SheetsApi:
    def __init__(self, sa_file=None):
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        path = sa_file or config.SERVICE_ACCOUNT_FILE
        if not path.exists():
            raise ApiAccessError(f"service-account key missing: {path}")
        creds = service_account.Credentials.from_service_account_file(
            str(path), scopes=SCOPES)
        self.http = AuthorizedSession(creds)
        self._meta: dict[str, list[dict]] = {}

    # -- transport with retry --------------------------------------------
    def _req(self, method: str, url: str, **kw):
        last = None
        for attempt in range(5):
            try:
                r = self.http.request(method, url, timeout=60, **kw)
            except Exception as e:               # network blip
                last = e
                time.sleep(2 * (attempt + 1))
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                last = RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
                time.sleep(3 * (attempt + 1))
                continue
            if r.status_code == 400 and "Office file" in r.text:
                raise OfficeFileError(
                    "This document is an uploaded Excel (.xlsx) file; the Sheets API "
                    "cannot edit it. Open it and use File -> Save as Google Sheets, "
                    "then put the new ID in config.py.")
            if r.status_code in (403, 404):
                raise ApiAccessError(
                    f"HTTP {r.status_code} — the robot account cannot open this sheet.\n"
                    f"  Fix: Share the sheet with {BOT_EMAIL} as Editor.\n"
                    f"  ({r.text[:200]})")
            if r.status_code >= 400:
                raise RuntimeError(f"Sheets API HTTP {r.status_code}: {r.text[:400]}")
            return r.json() if r.content else {}
        raise RuntimeError(f"Sheets API failed after retries: {last}")

    # -- metadata ----------------------------------------------------------
    def tabs(self, sid: str, refresh: bool = False) -> list[dict]:
        """[{title, gid, index, rows, cols}] leftmost first."""
        if refresh or sid not in self._meta:
            j = self._req("GET", f"{BASE}/{sid}",
                          params={"fields": "sheets.properties"})
            out = []
            for s in j.get("sheets", []):
                p = s["properties"]
                g = p.get("gridProperties", {})
                out.append({"title": p["title"], "gid": p["sheetId"],
                            "index": p.get("index", 0),
                            "rows": g.get("rowCount", 1000),
                            "cols": g.get("columnCount", 26)})
            out.sort(key=lambda t: t["index"])
            self._meta[sid] = out
        return self._meta[sid]

    def titles(self, sid: str, refresh: bool = True) -> list[str]:
        return [t["title"] for t in self.tabs(sid, refresh=refresh)]

    def gid(self, sid: str, tab: str) -> int:
        for t in self.tabs(sid, refresh=True):
            if t["title"] == tab:
                return t["gid"]
        raise KeyError(f"no tab named {tab!r}")

    def batch_update(self, sid: str, requests_: list[dict]) -> dict:
        r = self._req("POST", f"{BASE}/{sid}:batchUpdate",
                      json={"requests": requests_})
        self._meta.pop(sid, None)
        return r

    # -- values ------------------------------------------------------------
    def grid(self, sid: str, tab: str) -> list[list[str]]:
        """Whole tab as displayed text, row 1 = index 0 (TRUE sheet rows),
        padded to a rectangle (like the old gviz CSV)."""
        j = self._req("GET", f"{BASE}/{sid}/values/{quote(a1_range(tab), safe='')}",
                      params={"valueRenderOption": "FORMATTED_VALUE",
                              "majorDimension": "ROWS"})
        rows = [[("" if c is None else str(c)) for c in r] for r in j.get("values", [])]
        width = max((len(r) for r in rows), default=0)
        return [r + [""] * (width - len(r)) for r in rows]

    def write_cells(self, sid: str, tab: str, cells: dict[str, object]) -> None:
        """{'B2': 123, 'C2': '=A1*2'} typed as if by a user (USER_ENTERED)."""
        if not cells:
            return
        data = [{"range": a1_range(tab, ref), "values": [[v]]}
                for ref, v in cells.items()]
        self._req("POST", f"{BASE}/{sid}/values:batchUpdate",
                  json={"valueInputOption": "USER_ENTERED", "data": data})

    def cell_info(self, sid: str, tab: str, ref: str) -> dict:
        c, r = split_a1(ref)
        for t in self.tabs(sid):
            if t["title"] == tab and (r > t["rows"] or c > t["cols"]):
                return {}          # outside the grid = empty cell
        j = self._req("GET", f"{BASE}/{sid}", params={
            "ranges": a1_range(tab, ref), "includeGridData": "true",
            "fields": "sheets.data.rowData.values(userEnteredValue,effectiveValue,"
                      "formattedValue,effectiveFormat.numberFormat)"})
        try:
            return j["sheets"][0]["data"][0]["rowData"][0]["values"][0]
        except (KeyError, IndexError):
            return {}
