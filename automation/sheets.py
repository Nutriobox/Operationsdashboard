"""
Google Sheets wrapper (service account).

This is the module that deletes the worst code in the whole system. Compare:

  BEFORE (from daily-kot-comparison SKILL.md)
    - "Google Sheets cells are canvas-rendered; you cannot read cell values
       from the DOM. Read via the Name Box + formula bar... WAIT >=650ms before
       reading; 200-300ms causes lagged/shifted reads."
    - "SYNTHETIC Name Box navigation does NOT reliably move the grid selection
       for a paste target..."
    - "Build a TSV and copy it with a hidden textarea + execCommand('copy')...
       If a paste lands one row/column off, press ctrl+z to undo and reposition."
    - Reading 27 cells = 27 round trips at 650ms each.

  AFTER
    read_range(...)   -> 1 API call, all 27 cells
    write_range(...)  -> 1 API call, lands exactly where you asked
    duplicate_tab(...)-> 1 API call, no right-click coordinate hunting

Tabs are addressed by name; gids are resolved for you (which also happens to
solve the kot-latest.json pointer bug for free — see tab_gid()).
"""
from __future__ import annotations

from typing import Any, Sequence

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class Sheets:
    def __init__(self, service_account_file=None):
        path = service_account_file or config.SERVICE_ACCOUNT_FILE
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found.\n"
                "Create a service account, download its JSON key to that path, "
                "and share each sheet with the service account's email as Editor.\n"
                "See SETUP.md."
            )
        creds = service_account.Credentials.from_service_account_file(
            str(path), scopes=SCOPES
        )
        self.api = build("sheets", "v4", credentials=creds,
                         cache_discovery=False).spreadsheets()

    # -- metadata ----------------------------------------------------------
    def tabs(self, sheet_id: str) -> list[dict]:
        """[{title, gid, index}, ...] in visual order (leftmost first)."""
        meta = self.api.get(spreadsheetId=sheet_id,
                            fields="sheets.properties").execute()
        return [
            {
                "title": s["properties"]["title"],
                "gid": s["properties"]["sheetId"],
                "index": s["properties"]["index"],
            }
            for s in meta.get("sheets", [])
        ]

    def tab_titles(self, sheet_id: str) -> list[str]:
        return [t["title"] for t in self.tabs(sheet_id)]

    def tab_gid(self, sheet_id: str, title: str) -> int:
        for t in self.tabs(sheet_id):
            if t["title"] == title:
                return t["gid"]
        raise KeyError(f"tab {title!r} not found in {sheet_id}")

    def newest_tab(self, sheet_id: str) -> dict:
        """Leftmost tab — both KOT sheets keep newest-on-the-left."""
        return min(self.tabs(sheet_id), key=lambda t: t["index"])

    def has_tab(self, sheet_id: str, title: str) -> bool:
        return title in self.tab_titles(sheet_id)

    # -- read / write ------------------------------------------------------
    def read_range(self, sheet_id: str, a1: str,
                   formulas: bool = False) -> list[list[Any]]:
        """
        a1 like "'13th July'!A1:D11". One call, however many cells.
        formulas=True returns "=SUM(...)" instead of the computed value.
        """
        res = self.api.values().get(
            spreadsheetId=sheet_id,
            range=a1,
            valueRenderOption="FORMULA" if formulas else "UNFORMATTED_VALUE",
        ).execute()
        return res.get("values", [])

    def write_range(self, sheet_id: str, a1: str,
                    values: Sequence[Sequence[Any]]) -> int:
        """Write a rectangular block. Returns cells updated."""
        res = self.api.values().update(
            spreadsheetId=sheet_id,
            range=a1,
            valueInputOption="USER_ENTERED",   # so "=SUM(..)" and "12.5%" parse
            body={"values": [list(r) for r in values]},
        ).execute()
        return res.get("updatedCells", 0)

    def batch_write(self, sheet_id: str, blocks: dict[str, Sequence[Sequence[Any]]]) -> int:
        """
        Write several disjoint blocks in ONE request.
        blocks = {"'13th July'!B2:C10": [[...]], "'13th July'!A1": [["13th July"]]}
        """
        data = [{"range": a1, "values": [list(r) for r in vals]}
                for a1, vals in blocks.items()]
        res = self.api.values().batchUpdate(
            spreadsheetId=sheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": data},
        ).execute()
        return res.get("totalUpdatedCells", 0)

    # -- structure ---------------------------------------------------------
    def duplicate_tab(self, sheet_id: str, source_title: str,
                      new_title: str, index: int = 0) -> int:
        """
        Duplicate a tab and place it at `index` (0 = leftmost).
        Replaces the whole right-click -> Duplicate -> rename -> Move-left dance,
        including the "Delete sits right above Duplicate" coordinate hazard.
        Returns the new tab's gid.
        """
        src_gid = self.tab_gid(sheet_id, source_title)
        res = self.api.batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{
                "duplicateSheet": {
                    "sourceSheetId": src_gid,
                    "insertSheetIndex": index,
                    "newSheetName": new_title,
                }
            }]},
        ).execute()
        return res["replies"][0]["duplicateSheet"]["properties"]["sheetId"]

    def rename_tab(self, sheet_id: str, old: str, new: str):
        gid = self.tab_gid(sheet_id, old)
        self.api.batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{
                "updateSheetProperties": {
                    "properties": {"sheetId": gid, "title": new},
                    "fields": "title",
                }
            }]},
        ).execute()

    def move_tab(self, sheet_id: str, title: str, index: int):
        gid = self.tab_gid(sheet_id, title)
        self.api.batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{
                "updateSheetProperties": {
                    "properties": {"sheetId": gid, "index": index},
                    "fields": "index",
                }
            }]},
        ).execute()


def a1(tab: str, ref: str) -> str:
    """Quote a tab name safely: a1("Daily KOT Comparsion", "C5:L7")."""
    return f"'{tab}'!{ref}"
