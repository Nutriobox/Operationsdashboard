"""
Google Sheets writer — API edition (2026-09-23).

Same class name and method signatures as before (BrowserWriter), so none of the
jobs had to change. Under the hood it now talks to the Sheets API as the robot
service account (see sheets_api.py) instead of typing into a signed-in Chrome.
Result: no Google login to expire, no Name-Box drift, no profile lock.

Fallbacks (automatic):
  * sheet is still an uploaded .xlsx   -> old browser writer (sheet_writer_ui.py)
  * env NUTRIO_SHEETS_MODE=ui          -> old browser writer for everything
The old implementation is kept verbatim in sheet_writer_ui.py.
"""
from __future__ import annotations

import os

import sheets_api
from sheets_api import ApiAccessError, OfficeFileError


class SessionExpired(RuntimeError):
    """Kept for callers' except-clauses. Now means: robot can't open the sheet."""


class WriteError(RuntimeError):
    """A write did not land / verify."""


def _ui_mode() -> bool:
    return os.environ.get("NUTRIO_SHEETS_MODE", "").lower() == "ui"


class BrowserWriter:
    def __init__(self, headless: bool = True, timeout_ms: int = 45000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._api: sheets_api.SheetsApi | None = None
        self._ui = None                 # old UI writer, only if we must fall back
        self._active: str | None = None
        self._tab: str | None = None    # "selected" tab (the UI had one)

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self):
        if _ui_mode():
            self._start_ui()
        else:
            self._api = sheets_api.SheetsApi()
        return self

    def __exit__(self, *exc):
        if self._ui is not None:
            self._ui.__exit__(*exc)

    def _start_ui(self):
        import sheet_writer_ui
        print("sheet_writer: using the BROWSER (UI) writer")
        self._ui = sheet_writer_ui.BrowserWriter(headless=self.headless,
                                                 timeout_ms=self.timeout_ms)
        self._ui.__enter__()

    # -- workbook / tabs ---------------------------------------------------
    def open_book(self, sheet_id: str):
        if self._ui is not None:
            return self._ui.open_book(sheet_id)
        try:
            titles = self._api.titles(sheet_id)
        except OfficeFileError:
            print("sheet_writer: this workbook is an .xlsx — falling back to browser")
            self._start_ui()
            return self._ui.open_book(sheet_id)
        except ApiAccessError as e:
            raise SessionExpired(str(e)) from e
        self._active = sheet_id
        self._tab = titles[0] if titles else None

    def tab_titles(self) -> list[str]:
        if self._ui is not None:
            return self._ui.tab_titles()
        titles = self._api.titles(self._active)
        if not titles:
            raise SessionExpired("Read zero tabs from the workbook.")
        return titles

    def delete_tab(self, title: str) -> None:
        if self._ui is not None:
            return self._ui.delete_tab(title)
        if title not in self.tab_titles():
            return
        self._api.batch_update(self._active, [
            {"deleteSheet": {"sheetId": self._api.gid(self._active, title)}}])

    def purge_stray_copies(self) -> None:
        if self._ui is not None:
            return self._ui.purge_stray_copies()
        for t in [t for t in self.tab_titles() if t.startswith("Copy of ")]:
            print(f"SOURCE  purging stray tab {t!r}")
            self.delete_tab(t)

    def duplicate_tab(self, source_title: str, new_title: str) -> None:
        """Copy `source_title` to `new_title` and park it leftmost (newest-left)."""
        if self._ui is not None:
            return self._ui.duplicate_tab(source_title, new_title)
        self.purge_stray_copies()
        titles = self.tab_titles()
        if new_title in titles:
            gid = self._api.gid(self._active, new_title)
        else:
            if source_title not in titles or source_title.startswith("Copy of "):
                real = [t for t in titles if not t.startswith("Copy of ")]
                if not real:
                    raise WriteError("no real (non-copy) tab to duplicate from")
                source_title = real[0]
            src = self._api.gid(self._active, source_title)
            r = self._api.batch_update(self._active, [{"duplicateSheet": {
                "sourceSheetId": src, "insertSheetIndex": 0,
                "newSheetName": new_title}}])
            gid = r["replies"][0]["duplicateSheet"]["properties"]["sheetId"]
        self._api.batch_update(self._active, [{"updateSheetProperties": {
            "properties": {"sheetId": gid, "index": 0}, "fields": "index"}}])
        if self.tab_titles()[0] != new_title:
            raise WriteError(f"{new_title!r} did not end up leftmost")
        self._tab = new_title

    def select_tab(self, title: str) -> None:
        if self._ui is not None:
            return self._ui.select_tab(title)
        if title not in self.tab_titles():
            raise WriteError(f"no tab named {title!r}")
        self._tab = title

    # -- cell reads / writes ----------------------------------------------
    def _need_tab(self) -> str:
        if not self._tab:
            raise WriteError("no tab selected — call select_tab() first")
        return self._tab

    def read_selected_value(self, ref: str) -> str:
        """What the formula bar would show for `ref` on the selected tab."""
        if self._ui is not None:
            return self._ui.read_selected_value(ref)
        info = self._api.cell_info(self._active, self._need_tab(), ref)
        uev = info.get("userEnteredValue", {})
        if "formulaValue" in uev:
            return uev["formulaValue"]
        if "stringValue" in uev:
            return uev["stringValue"]
        if "boolValue" in uev:
            return "TRUE" if uev["boolValue"] else "FALSE"
        if "numberValue" in uev:
            ftype = (info.get("effectiveFormat", {}).get("numberFormat", {})
                     .get("type", ""))
            if ftype in ("DATE", "TIME", "DATE_TIME", "PERCENT"):
                return info.get("formattedValue", "")
            n = uev["numberValue"]
            return str(int(n)) if float(n).is_integer() else repr(n)
        return ""

    def write_rows_down(self, top_left: str, rows: list[list]) -> None:
        """Write a block starting at `top_left`; blank/None cells left untouched."""
        if self._ui is not None:
            return self._ui.write_rows_down(top_left, rows)
        c0, r0 = sheets_api.split_a1(top_left)
        cells = {}
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                if val is None or val == "":
                    continue
                cells[f"{sheets_api.num_to_col(c0 + c)}{r0 + r}"] = val
        self._api.write_cells(self._active, self._need_tab(), cells)

    def write_cell(self, ref: str, value) -> None:
        if self._ui is not None:
            return self._ui.write_cell(ref, value)
        if value is None or value == "":
            return          # typing nothing + Enter never changed the cell either
        self._api.write_cells(self._active, self._need_tab(), {ref: value})

    def _grid_range(self, ref: str) -> dict:
        c, r = sheets_api.split_a1(ref)
        return {"sheetId": self._api.gid(self._active, self._need_tab()),
                "startRowIndex": r - 1, "endRowIndex": r,
                "startColumnIndex": c - 1, "endColumnIndex": c}

    def format_percent(self, ref: str) -> None:
        if self._ui is not None:
            return self._ui.format_percent(ref)
        self._api.batch_update(self._active, [{"repeatCell": {
            "range": self._grid_range(ref),
            "cell": {"userEnteredFormat": {"numberFormat": {
                "type": "PERCENT", "pattern": "0.00%"}}},
            "fields": "userEnteredFormat.numberFormat"}}])

    def copy_format(self, src: str, dst: str) -> None:
        """Ctrl+C / Ctrl+V equivalent (values, formulas re-anchored, formats)."""
        if self._ui is not None:
            return self._ui.copy_format(src, dst)
        self._api.batch_update(self._active, [{"copyPaste": {
            "source": self._grid_range(src), "destination": self._grid_range(dst),
            "pasteType": "PASTE_NORMAL"}}])

    # -- verification ------------------------------------------------------
    def read_tab(self, tab: str) -> list[list[str]]:
        """Displayed values; list index == true sheet row - 1."""
        if self._ui is not None:
            return self._ui.read_tab(tab)
        assert self._active, "open_book() first"
        return self._api.grid(self._active, tab)
