"""
Playwright *writer* for Google Sheets — same signed-in profile the readers use
(secrets/browser-profile, the mayank@nutriobox.com Google session).

Why a browser instead of the Sheets API: the daily-KOT destination workbook
("Sales Data") is an uploaded Excel (.xlsx) file living in Drive, and the Sheets
API refuses those ("This operation is not supported for this document. The
document must not be an Office file."). So both the native source sheet and the
xlsx destination are written through the Google Sheets *web UI*, as the user.

Why this succeeds where the Claude-in-Chrome run failed (23 Aug 2026): that run
was blocked on tab duplication because (1) CDP captureScreenshot froze while the
tab context menu was open, (2) the viewport kept resizing between tool calls so
screenshot-derived coordinates went stale, and (3) synthetic DOM events were
rejected as untrusted. Headless Playwright has none of those failure modes: a
FIXED viewport, no screenshot dependency, and real *trusted* mouse/keyboard
events that the menu accepts.

Write technique (deliberately canvas-free):
  - Navigate the selection with the Name Box (#t-name-box), a real DOM input:
    fill "B2", press Enter, and the grid selection jumps there.
  - Enter values with the real keyboard: type a value, press Tab to move right or
    Enter to move down. Google Sheets' Tab-then-Enter returns to the row's start
    column on the next row, so a block writes in reading order without any
    click-by-pixel.
  - Every write is read back through gviz (BrowserReader) and compared; a
    mismatch raises before anything downstream trusts the sheet.

Tab creation (source sheet only) uses trusted right-click -> "Duplicate", a
double-click rename, and right-click -> "Move left" to park the new tab at the
left edge (newest-on-the-left, matching sheets.py::newest_tab).
"""
from __future__ import annotations

import csv
import io
import time
from urllib.parse import quote

import config

PROFILE_DIR = config.SECRETS / "browser-profile"
EDIT_URL = "https://docs.google.com/spreadsheets/d/{sid}/edit"
GVIZ_URL = ("https://docs.google.com/spreadsheets/d/{sid}/gviz/tq"
            "?tqx=out:csv&sheet={tab}&headers=0")


class SessionExpired(RuntimeError):
    """The profile is not signed in to Google."""


class WriteError(RuntimeError):
    """A UI write did not land / verify."""


_TAB_JS = """() => Array.from(
    document.querySelectorAll('.docs-sheet-tab .docs-sheet-tab-name')
).map(e => e.textContent.trim())"""


class BrowserWriter:
    """
    One signed-in Google session for a run. Open a workbook with open_book(),
    then use the tab / cell helpers. Values are always read back and verified.
    """

    def __init__(self, headless: bool = True, timeout_ms: int = 45000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = self._ctx = self._page = None
        self._active: str | None = None

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        try:
            self._ctx = self._pw.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=self.headless,
                viewport={"width": 1600, "height": 1000},   # fixed: no resize drift
                args=["--disable-blink-features=AutomationControlled",
                      "--window-size=1600,1000"],
            )
        except Exception as e:
            self._pw.stop()
            if "ProcessSingleton" in str(e) or "SingletonLock" in str(e):
                raise SessionExpired(
                    "The browser profile is locked — another job is using it, or a "
                    "crashed run left a lock behind. Wait and retry.") from e
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

    # -- workbook / tabs ---------------------------------------------------
    def open_book(self, sheet_id: str):
        """Open a workbook and wait for its tab strip to settle."""
        page = self._page
        # Google Sheets navigation occasionally fails with a transient network
        # error (net::ERR_CONNECTION_RESET, ERR_TIMED_OUT, ...). A single such
        # failure used to abort the whole run BEFORE any write — this is how the
        # 13th Sep daily fill was lost (14 Sep run: ERR_CONNECTION_RESET at
        # open_book). Retry the navigation a few times before giving up; a
        # genuine auth redirect is still handled immediately below.
        url = EDIT_URL.format(sid=sheet_id)
        for attempt in range(4):
            try:
                page.goto(url, wait_until="domcontentloaded")
                break
            except Exception as e:  # retry transient network errors only
                msg = str(e)
                transient = any(s in msg for s in (
                    "ERR_CONNECTION_RESET", "ERR_NETWORK_CHANGED",
                    "ERR_CONNECTION_CLOSED", "ERR_CONNECTION_TIMED_OUT",
                    "ERR_TIMED_OUT", "ERR_INTERNET_DISCONNECTED",
                    "ERR_NAME_NOT_RESOLVED", "Timeout",
                ))
                if not transient or attempt == 3:
                    raise
                print(f"open_book: navigation failed ({msg.splitlines()[0]}); "
                      f"retry {attempt + 1}/3")
                page.wait_for_timeout(2000 * (attempt + 1))
        if "accounts.google.com" in page.url or "/ServiceLogin" in page.url:
            raise SessionExpired(
                "The browser profile is not signed in to Google.\n"
                "  Fix: run  DELAY-LOGIN.bat  and sign in as the account that can "
                "edit the KOT sheets, then close the window.")
        page.wait_for_selector(".docs-sheet-tab", timeout=self.timeout_ms)
        # tab strip renders progressively on big workbooks
        prev, stable = -1, 0
        for _ in range(20):
            n = len(page.evaluate(_TAB_JS))
            stable = stable + 1 if n == prev else 0
            if stable >= 2 and n > 0:
                break
            prev = n
            page.wait_for_timeout(500)
        self._active = sheet_id
        # Make sure the grid has focus for keyboard nav.
        page.wait_for_timeout(800)

    def tab_titles(self) -> list[str]:
        titles = self._page.evaluate(_TAB_JS)
        if not titles:
            raise SessionExpired("Read zero tabs — the workbook did not render.")
        return titles

    def _tab_handle(self, title: str):
        return self._page.locator(
            ".docs-sheet-tab", has=self._page.locator(
                ".docs-sheet-tab-name", has_text=title)
        ).first

    def _context_menu_click(self, item_text: str):
        """Click an item in whatever context menu is currently open (trusted)."""
        page = self._page
        page.wait_for_selector(".goog-menuitem:visible", timeout=self.timeout_ms)
        page.get_by_role("menuitem", name=item_text, exact=False).first.click(
            timeout=self.timeout_ms)

    def delete_tab(self, title: str) -> None:
        """Right-click a tab -> Delete -> confirm 'OK'. No-op if the tab is gone.

        Used to purge leftover 'Copy of ...' tabs. Deleting a sheet that holds
        data pops a "Heads up! Are you sure...?" confirm; a blank one may delete
        with no dialog, so the OK click is best-effort.
        """
        page = self._page
        if title not in self.tab_titles():
            return
        self._tab_handle(title).click(button="right")
        page.wait_for_timeout(400)
        try:
            # Exact match: the tab menu's item is exactly "Delete"; never let this
            # fall through to a grid menu's "Delete row"/"Delete column".
            page.wait_for_selector(".goog-menuitem:visible", timeout=self.timeout_ms)
            page.get_by_role("menuitem", name="Delete", exact=True).first.click(
                timeout=self.timeout_ms)
        except Exception:
            page.keyboard.press("Escape")
            return
        page.wait_for_timeout(600)
        try:
            page.get_by_role("button", name="OK", exact=True).first.click(
                timeout=self.timeout_ms)
        except Exception:
            pass                          # deleted without a confirm dialog
        page.wait_for_timeout(800)

    def purge_stray_copies(self) -> None:
        """Delete every 'Copy of ...' tab left behind by an earlier failed run.

        Orphaned copies were the 4-11 Sep 2026 pileup: a slow-but-successful
        Duplicate got retried into a SECOND copy, one was renamed to the date and
        the other stranded. Clearing them at the top of each duplication keeps
        them from accumulating AND from ever being chosen as the template.
        """
        for t in [t for t in self.tab_titles() if t.startswith("Copy of ")]:
            print(f"SOURCE  purging stray tab {t!r}")
            self.delete_tab(t)

    def duplicate_tab(self, source_title: str, new_title: str) -> None:
        """Purge strays, right-click a real tab -> Duplicate, rename, move left."""
        page = self._page

        # (1) Remove any orphaned 'Copy of ...' tabs before we start, so they can
        #     neither accumulate nor be picked as the template below.
        self.purge_stray_copies()

        # If the caller's chosen template was itself a stray copy (or vanished in
        # the purge), fall back to the newest real (non-copy) tab.
        titles = self.tab_titles()
        if source_title not in titles or source_title.startswith("Copy of "):
            real = [t for t in titles if not t.startswith("Copy of ")]
            if not real:
                raise WriteError("no real (non-copy) tab to duplicate from")
            source_title = real[0]

        # (2) Duplicate the source tab. Google usually names the copy
        # "Copy of <source_title>", but that can vary (locale/UI changes) and the
        # right-click occasionally doesn't register, so we detect the NEW tab by
        # diffing the tab list and retry the whole action if nothing appeared.
        #
        # The retry used to fire after a single fixed wait — on this heavy .xlsx
        # workbook the new tab often hadn't rendered yet, so a SUCCESSFUL
        # duplicate was retried and produced a second orphan copy (the 4-11 Sep
        # 2026 stray-tab pileup). Now we POLL for the new tab for several seconds
        # before deciding it failed, and if more than one copy appears we keep one
        # and delete the extras.
        before = self.tab_titles()
        copy_title = None
        for attempt in range(3):
            self._tab_handle(source_title).click(button="right")
            page.wait_for_timeout(400)
            try:
                self._context_menu_click("Duplicate")
            except Exception:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                continue
            new = []
            for _ in range(16):           # up to ~8s for the copy to render
                page.wait_for_timeout(500)
                new = [t for t in self.tab_titles() if t not in before]
                if new:
                    break
            if new:
                preferred = f"Copy of {source_title}"
                copy_title = preferred if preferred in new else new[0]
                for extra in [t for t in new if t != copy_title]:
                    print(f"SOURCE  removing extra duplicate {extra!r}")
                    self.delete_tab(extra)
                break
            page.wait_for_timeout(800)    # nothing appeared; retry the duplicate
        if copy_title is None:
            raise WriteError(
                f"duplicate of {source_title!r} produced no new tab after 3 tries; "
                f"tabs now: {self.tab_titles()}")

        # (3) Rename: double-click the copy, select all, type the new name. The
        #     dblclick doesn't always enter edit mode on a laggy workbook, so
        #     retry a few times rather than abort (which would strand the copy).
        renamed = False
        for attempt in range(3):
            if new_title in self.tab_titles():
                renamed = True
                break
            copy_tab = self._tab_handle(copy_title)
            copy_tab.dblclick()
            page.wait_for_timeout(300)
            page.keyboard.press("Control+A")
            page.keyboard.type(new_title, delay=20)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000 + 400 * attempt)
        if not renamed and new_title not in self.tab_titles():
            # Leave the copy for the next run's purge rather than a half-named tab.
            self.delete_tab(copy_title)
            raise WriteError(f"rename to {new_title!r} did not take")

        # (4) Move to leftmost so 'newest' stays on the left.
        for _ in range(len(self.tab_titles())):
            if self.tab_titles()[0] == new_title:
                break
            self._tab_handle(new_title).click(button="right")
            try:
                self._context_menu_click("Move left")
            except Exception:
                page.keyboard.press("Escape")
                break
            page.wait_for_timeout(500)

    def select_tab(self, title: str) -> None:
        self._tab_handle(title).click()
        self._page.wait_for_timeout(600)

    # -- cell writes -------------------------------------------------------
    def _goto_cell(self, ref: str) -> None:
        """Jump the selection to a cell via the Name Box (trusted DOM input).

        Verifies the Name Box actually reports `ref` after navigating — a mis-fired
        navigation that silently lands one cell away is exactly how a whole row got
        overwritten before, so we confirm and retry rather than type blind.

        Keystrokes go through the Name Box *locator* (box.press / box.type), not
        page.keyboard: on this heavy .xlsx workbook a bare click did not reliably
        hold focus in the box, so page-level typing leaked into the grid and the
        selection never moved off A1 ("reads 'A1'" failure). Locator-scoped keys
        auto-focus the input, so the ref can't miss (fixed 2026-09-09)."""
        page = self._page
        want = ref.strip().upper()
        sel = ""
        for attempt in range(5):
            # Clear any stray context menu / overlay that could swallow the click.
            page.keyboard.press("Escape")
            box = page.locator("#t-name-box")
            try:
                box.click(timeout=self.timeout_ms)
            except Exception:
                page.wait_for_timeout(400)
                continue
            # Clear + type + commit, all targeting the input element itself.
            box.press("Control+A")
            box.press("Delete")
            box.type(ref, delay=30)
            box.press("Enter")
            page.wait_for_timeout(500 + 250 * attempt)   # let the grid settle
            sel = page.evaluate(
                "() => {var b=document.querySelector('#t-name-box');"
                "return b ? (b.value || b.textContent || '') : '';}") or ""
            if sel.strip().upper().split(":")[0] == want:
                return
            page.wait_for_timeout(300)
        raise WriteError(
            f"Name Box did not land on {ref!r} (reads {sel!r}) after 5 tries — "
            "refusing to type into the wrong cell.")

    def read_selected_value(self, ref: str) -> str:
        """Live value of `ref` straight from the formula bar (reflects the true
        sheet, unlike gviz which can be cached or row-misaligned)."""
        self._goto_cell(ref)
        return self._page.evaluate(
            "() => {var fb=document.querySelector('#t-formula-bar-input');"
            "return fb ? fb.textContent : '';}") or ""

    def write_rows_down(self, top_left: str, rows: list[list]) -> None:
        """
        Write a rectangular block starting at `top_left` (e.g. "B2"), row by row.

        Each cell is addressed ABSOLUTELY through the Name Box (_goto_cell) and then
        typed — we no longer type across a row pressing Tab between cells. Blind Tab
        navigation was the source of an intermittent one-column drift: under load a
        single Tab keystroke could be dropped, shifting every later value in that row
        one column to the left (e.g. the AOV formula =(L*0.95)/R landing in the Orders
        column and self-referencing into #REF!, and Discounts/Zomato values falling
        off the end). _goto_cell verifies the Name Box actually landed on the target
        and retries, so an absolute write cannot drift. Cost is one Name Box hop per
        cell, which is fine for these unattended daily/weekly writes (fixed 2026-09-11).
        """
        page = self._page

        def _split(a1: str):
            a1 = a1.strip().upper()
            i = 0
            while i < len(a1) and a1[i].isalpha():
                i += 1
            return a1[:i], int(a1[i:])

        def _col_to_num(letters: str) -> int:
            n = 0
            for ch in letters:
                n = n * 26 + (ord(ch) - 64)
            return n

        def _num_to_col(n: int) -> str:
            s = ""
            while n > 0:
                n, rem = divmod(n - 1, 26)
                s = chr(65 + rem) + s
            return s

        start_col_letters, start_row = _split(top_left)
        start_col = _col_to_num(start_col_letters)

        for r, row in enumerate(rows):
            rownum = start_row + r
            for c, val in enumerate(row):
                if val is None or val == "":
                    continue   # blank cells (e.g. the M notes column) are left untouched
                ref = f"{_num_to_col(start_col + c)}{rownum}"
                self._goto_cell(ref)             # verified Name Box hop — cannot drift
                page.keyboard.type(str(val), delay=12)
                page.keyboard.press("Enter")
                page.wait_for_timeout(120)
        page.wait_for_timeout(600)   # let autosave flush

    def write_cell(self, ref: str, value) -> None:
        self._goto_cell(ref)
        self._page.keyboard.type("" if value is None else str(value), delay=12)
        self._page.keyboard.press("Enter")
        self._page.wait_for_timeout(400)

    def format_percent(self, ref: str) -> None:
        """
        Apply Sheets' percent format (Ctrl+Shift+5) to `ref`.

        Needed by daily_sheet.py: a ratio formula such as =N50/L50 renders as
        0.9054 until the cell carries the percent format, and the Daily
        Dashboard sheet expects 90.54%.
        """
        self._goto_cell(ref)
        self._page.keyboard.press("Control+Shift+Digit5")
        self._page.wait_for_timeout(300)

    def copy_format(self, src: str, dst: str) -> None:
        """
        Copy `src` onto `dst` so `dst` inherits its number format.

        The Daily Dashboard's AOV column (S) must display as a whole integer;
        the sheet's own convention is to copy the cell above rather than set a
        format explicitly, so the column stays visually consistent.
        """
        self._goto_cell(src)
        self._page.keyboard.press("Control+C")
        self._page.wait_for_timeout(250)
        self._goto_cell(dst)
        self._page.keyboard.press("Control+V")
        self._page.wait_for_timeout(400)
        self._page.keyboard.press("Escape")
        self._page.wait_for_timeout(150)

    # -- verification (read back through gviz) -----------------------------
    def read_tab(self, tab: str) -> list[list[str]]:
        assert self._active, "open_book() first"
        # Cache-buster: gviz CSV export caches on the URL, so a read-back moments
        # after a write can otherwise return the pre-write snapshot and trigger a
        # false "verify failed". A unique param forces a fresh export every time.
        url = (GVIZ_URL.format(sid=self._active, tab=quote(tab, safe=""))
               + f"&_cb={time.time_ns()}")
        resp = self._ctx.request.get(url, timeout=self.timeout_ms)
        if resp.status != 200:
            raise SessionExpired(f"gviz HTTP {resp.status} for tab {tab!r}")
        body = resp.text()
        if body.lstrip().startswith("<"):
            raise SessionExpired("gviz returned the Google sign-in page — not logged in.")
        return [row for row in csv.reader(io.StringIO(body))]
