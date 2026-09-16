"""
Petpooja HTTP client.

Replaces the browser-driving in daily-kot-comparison / kot-comparsion /
petpooja-sales-to-gsheet / nutriobox-daily-data-v2 / etc.

All contracts below were captured live from billing.petpooja.com on 14 Jul 2026
by inspecting the real network traffic — not guessed:

  outlet switch   POST /                                header_changed_rest_id=<id>
  KOT count       POST /items/kot_list/                 data[Kot][startdate]
                                                        data[Kot][enddate]
                                                        data[Kot][order_type][]  (2=Pick Up, 3=Dine In)
                                  -> HTML: "Showing 1 to X of N records"
  custom report   POST /custom_reports/get_data_query/{group}/{report}
                                  -> filter fields are id'd re_filter_filed_{group}_{report}_{i}_{from|to}

The custom-report body is rebuilt from the report page's own form each call, so
if Petpooja renames a filter field the client follows it instead of breaking.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

import config


class SessionExpired(RuntimeError):
    """Petpooja cookie is dead — re-run refresh_tokens.py."""


class ScrapeError(RuntimeError):
    """Page loaded but we couldn't find the number we needed."""


LOGIN_MARKERS = ("name=\"data[User][password]\"", "id=\"UserLoginForm\"", "/users/login")


@dataclass
class KotResult:
    outlet_id: int
    total_kot: int
    captain_kot: int

    @property
    def captain_pct(self) -> float:
        if not self.total_kot:
            return 0.0
        return round(self.captain_kot / self.total_kot * 100, 2)


class Petpooja:
    def __init__(self, cookie: str, timeout: int = 45):
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/150.0.0.0 Safari/537.36"),
            "Accept-Language": "en-GB,en;q=0.9",
        })
        self.s.headers["Cookie"] = cookie
        self.timeout = timeout
        self._current_outlet: int | None = None

    # -- plumbing ----------------------------------------------------------
    @classmethod
    def from_tokens(cls, path=None):
        path = path or config.TOKENS_FILE
        try:
            tok = json.loads(path.read_text())
        except FileNotFoundError:
            raise SessionExpired(
                f"{path} not found. Run:  python refresh_tokens.py"
            )
        cookie = tok.get("petpooja_cookie")
        if not cookie:
            raise SessionExpired("petpooja_cookie missing from tokens.json")
        return cls(cookie)

    def _check_alive(self, html: str):
        if any(m in html for m in LOGIN_MARKERS):
            raise SessionExpired(
                "Petpooja bounced us to the login page. "
                "Run:  python refresh_tokens.py"
            )

    def _get(self, path: str) -> str:
        r = self.s.get(config.PETPOOJA_BASE + path, timeout=self.timeout)
        r.raise_for_status()
        self._check_alive(r.text)
        return r.text

    def _post(self, path: str, data, **kw) -> requests.Response:
        r = self.s.post(config.PETPOOJA_BASE + path, data=data,
                        timeout=self.timeout, **kw)
        r.raise_for_status()
        return r

    # -- outlet switching --------------------------------------------------
    def switch_outlet(self, outlet_id: int, settle: float = 1.0):
        """
        Petpooja keeps the 'current outlet' in the server session. The UI does
        this by submitting a hidden form (#change_res) to the site root.
        """
        if self._current_outlet == outlet_id:
            return
        r = self._post("/", {"header_changed_rest_id": str(outlet_id)})
        self._check_alive(r.text)
        self._current_outlet = outlet_id
        # Petpooja needs a beat to commit the switch server-side. The old
        # browser flow slept 10s; over plain HTTP ~1s is plenty, but we verify
        # below anyway so this is belt-and-braces, not superstition.
        time.sleep(settle)

    def _assert_outlet(self, html: str, expected: int):
        m = re.search(r'id="selected_restaurant_id"[^>]*value="(\d+)"', html)
        if not m:
            m = re.search(r'value="(\d+)"[^>]*id="selected_restaurant_id"', html)
        if m and int(m.group(1)) != expected:
            raise ScrapeError(
                f"outlet mismatch: asked for {expected} "
                f"({config.SHORT.get(expected)}), page is showing {m.group(1)}"
            )

    # -- KOT count ---------------------------------------------------------
    def kot_count(self, outlet_id: int, start: str, end: str,
                  order_types=(config.ORDER_TYPE_PICKUP, config.ORDER_TYPE_DINEIN)) -> int:
        """
        Total KOTs for the window, filtered to the given order types.

        start/end are Petpooja's KOT format: "13 Jul 2026 01:00:00"

        NB: the old skill warned that a *native* form submit ignores order_type
        and returns ALL types. That was a DOM quirk — over HTTP we post the
        fields directly, so the filter is always honoured. Verified: DLF Phase 2
        on 13 Jul returns 37 for [Pick Up, Dine In].

        UPDATE 2026-08-24: Petpooja split the KOT list into a page shell
        (/items/kot_list/) and an AJAX results fragment (/items/klist/). Posting
        the filters to /items/kot_list/ now returns the shell with no "Showing
        1..N" line, so we POST to /items/klist/ with the fragment's full field
        set (restaurant_id + current_page_url + XHR/Referer headers). The results
        HTML — including "Showing 1 to X of N records" — comes back from klist.
        Re-verified: DLF Phase 2, 13 Jul, [Pick Up, Dine In] -> 37.

        NB: /items/klist/ returns the one-byte sentinel "9" ("reload the parent
        page") unless the /items/kot_list/ shell has been loaded first in the
        same session — the shell sets the server-side page context klist checks.
        So we prime the shell with a GET before POSTing the filters.
        """
        self.switch_outlet(outlet_id)

        payload = [
            ("data[Kot][startdate]", start),
            ("data[Kot][enddate]", end),
            ("data[Kot][order_type]", ""),      # hidden companion field
            ("data[Kot][kot_id]", ""),
            ("data[Kot][customer_name]", ""),
            ("data[Kot][customer_phone]", ""),
            ("data[Kot][table_no]", ""),
            ("data[restaurant_id]", str(outlet_id)),
            ("data[current_page_url]", config.PETPOOJA_BASE + "/items/kot_list/"),
        ]
        for ot in order_types:
            payload.append(("data[Kot][order_type][]", ot))

        # klist returns the sentinel "9" ("reload the parent page") until the
        # kot_list shell has been (re)loaded in the session AND the outlet switch
        # has committed server-side. On this shared live account another task can
        # flip the current outlet mid-sequence (the "outlet-session collision"
        # the old skills warned about), so each retry RE-SWITCHES the outlet, then
        # re-primes the shell, before POSTing again — with a growing back-off.
        html = ""
        for attempt in range(6):
            if attempt:
                self._current_outlet = None          # force a real re-switch
                self.switch_outlet(outlet_id, settle=1.5)
            self._get("/items/kot_list/")            # prime server-side page context
            r = self._post(
                "/items/klist/",
                payload,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": config.PETPOOJA_BASE + "/items/kot_list/",
                },
            )
            html = r.text
            if html.strip() != "9" and len(html) > 20:
                break
            time.sleep(1.5 + attempt)  # switch not committed yet; settle and retry

        self._check_alive(html)

        if re.search(r"No Results Found", html, re.I):
            return 0

        m = re.search(r"Showing[^<\n]*?of\s+([0-9,]+)\s+(?:records|entries)", html, re.I)
        if not m:
            raise ScrapeError(
                f"KOT count not found for {config.SHORT.get(outlet_id)} "
                f"({start} -> {end}); klist returned {html[:40]!r}. "
                "Petpooja may have changed the results table."
            )
        return int(m.group(1).replace(",", ""))

    # -- custom reports ----------------------------------------------------
    def _report_form(self, view_id: int):
        """
        Load a custom report page and reverse its own form.

        Returns (group, report, fields) where `fields` is the POST body the page
        itself would send. Filter inputs carry ids but no name attributes, so we
        key them by id — which is exactly what Petpooja's own JS does.
        """
        # Petpooja intermittently serves a redirect stub instead of the report
        # HTML (the same SPA gating that hit KOT/Captain), which has no
        # re_filter_filed_* inputs. It's transient, so retry the GET a few times
        # before giving up.
        soup = None
        m = None
        for attempt in range(4):
            html = self._get(f"/custom_reports/view_report/{view_id}")
            soup = BeautifulSoup(html, "html.parser")
            ids = [el.get("id", "") for el in soup.select('[id^="re_filter_filed_"]')]
            for i in ids:
                m = re.match(r"re_filter_filed_(\d+)_(\d+)_", i)
                if m:
                    break
            if m:
                break
            time.sleep(1.5 * (attempt + 1))
        if not m:
            raise ScrapeError(
                f"view_report/{view_id}: no re_filter_filed_* inputs found after "
                "4 tries. Petpooja may have changed this report."
            )
        group, report = int(m.group(1)), int(m.group(2))

        fields: dict[str, str] = {}
        for el in soup.find_all(["input", "select"]):
            eid, name = el.get("id", ""), el.get("name")
            val = el.get("value", "") or ""
            if name:
                fields[name] = val
            if eid.startswith("re_filter_filed_") or eid in (
                "selected_from_date", "selected_end_date", "selected_restaurant_id"
            ):
                fields[eid] = val
        return group, report, fields

    def custom_report(self, view_id: int, outlet_id: int,
                      from_dt: str, to_dt: str) -> BeautifulSoup:
        """
        Run a custom report and return its rendered result as soup.
        from_dt/to_dt use Petpooja's report format: "2026-07-13 01:00:00"
        """
        self.switch_outlet(outlet_id)
        group, report, fields = self._report_form(view_id)

        # Stamp the date range into every from/to field the page exposes.
        for k in list(fields):
            if k.endswith("_from") or k == "selected_from_date":
                fields[k] = from_dt
            elif k.endswith("_to") or k == "selected_end_date":
                fields[k] = to_dt
        fields["selected_restaurant_id"] = str(outlet_id)

        r = self._post(
            f"/custom_reports/get_data_query/{group}/{report}",
            fields,
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        body = r.text
        self._check_alive(body)

        # The endpoint returns either raw HTML or JSON wrapping HTML.
        if body.lstrip().startswith("{"):
            try:
                payload = r.json()
                for key in ("html", "data", "content", "result"):
                    if isinstance(payload.get(key), str):
                        body = payload[key]
                        break
            except ValueError:
                pass
        return BeautifulSoup(body, "html.parser")

    def captain_kots(self, outlet_id: int, from_dt: str, to_dt: str) -> int:
        """
        Captain App KOT count = the 'No of Kots' cell on the report's Total row.
        Verified: Rajinder Nagar on 13 Jul returns 61.
        """
        soup = self.custom_report(config.REPORT_CAPTAIN_PERFORMANCE,
                                  outlet_id, from_dt, to_dt)

        if re.search(r"No Record Found", soup.get_text(), re.I):
            return 0

        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            kot_idx = next(
                (i for i, h in enumerate(headers) if re.search(r"no\s*of\s*kots", h, re.I)),
                None,
            )
            if kot_idx is None:
                continue
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue
                if re.search(r"total", cells[0].get_text(strip=True), re.I):
                    if kot_idx < len(cells):
                        raw = cells[kot_idx].get_text(strip=True).replace(",", "")
                        return int(float(raw or 0))
        raise ScrapeError(
            f"Captain 'Total' row not found for {config.SHORT.get(outlet_id)} "
            f"({from_dt} -> {to_dt})."
        )

    # -- add-ons report (view_report/31 -> get_data_query/1/23) -------------
    def addons(self, outlet_id: int, date_ymd: str) -> list[dict]:
        """
        Per-outlet add-on pivot for a single day.

        Returns a list of {addonGroup, addonItem, qty, total}, already
        collapsed to one row per (group, item). Mirrors the old browser scrape
        of `#re_pivot_table_1`: the group cell is only printed on its first row,
        so we carry it down; the trailing Total / Sub Total / Min / Max / Avg
        rows are dropped and used only to VERIFY our sums.

        `date_ymd` is 'YYYY-MM-DD' (the addon filter takes a plain date).
        Raises ScrapeError if our summed qty/total don't match the page Total.
        """
        soup = self.custom_report(config.REPORT_ADDONS, outlet_id,
                                  date_ymd, date_ymd)

        if re.search(r"No Record Found", soup.get_text(), re.I):
            return []

        table = soup.find(id="re_pivot_table_1")
        if table is None:
            # Fallback: any table carrying a 'Total' row with >=5 columns.
            for t in soup.find_all("table"):
                if re.search(r"\bTotal\b", t.get_text()):
                    table = t
                    break
        if table is None:
            raise ScrapeError(
                f"addon pivot not found for {config.SHORT.get(outlet_id)} "
                f"({date_ymd}). Petpooja may have changed report 31."
            )

        SKIP = {"total", "min.", "max.", "avg.", "sub total"}
        grouped: dict[tuple, dict] = {}
        page_total = None
        current_group = ""

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 5:
                continue
            c = [x.get_text(strip=True) for x in cells]
            first = c[0].strip()
            if first.lower() == "total":
                page_total = (_num(c[3]), _num(c[4]))
                continue
            if first.lower() in SKIP:
                continue
            if first:
                current_group = first
            addon_item, name = c[1].strip(), c[2].strip()
            if not addon_item or not name:
                continue
            qty, tot = _num(c[3]), _num(c[4])
            key = (current_group, addon_item)
            g = grouped.setdefault(key, {"addonGroup": current_group,
                                         "addonItem": addon_item,
                                         "qty": 0.0, "total": 0.0})
            g["qty"] += qty
            g["total"] += tot

        rows = list(grouped.values())

        # Verify against the page's own Total row (same guard as the old scrape).
        if page_total is not None:
            sum_q = round(sum(r["qty"] for r in rows))
            sum_s = round(sum(r["total"] for r in rows))
            if sum_q != round(page_total[0]) or sum_s != round(page_total[1]):
                raise ScrapeError(
                    f"addon sum mismatch for {config.SHORT.get(outlet_id)} "
                    f"({date_ymd}): summed qty/total {sum_q}/{sum_s} "
                    f"vs page Total {round(page_total[0])}/{round(page_total[1])}"
                )
        return rows

    # -- POS dashboard reconciliation (morning only) -----------------------
    def pos_dashboard_total(self) -> dict:
        """
        Read the 'All Outlet Statistics -> Total Sales' grand total off
        /users/dashboard. Over HTTP the dashboard renders its default window,
        which at ~4 AM IST is 'yesterday' = the morning run's target_date; the
        caller MUST confirm `displayed_date` matches target_date before trusting
        `total`. Best-effort per-outlet map is returned when readable.

        Returns {total: float|None, by_outlet: {name: float}, displayed_date: str|None}.
        """
        html = self._get("/users/dashboard")
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        displayed_date = None
        m = re.search(r"(\d{1,2}(?:st|nd|rd|th)\s+[A-Za-z]{3,9}(?:\s+\d{4})?)", text)
        if m:
            displayed_date = m.group(1)

        total = None
        m = re.search(r"Total\s+Sales[^0-9]{0,40}([0-9][0-9,]*\.?\d*)", text, re.I)
        if m:
            total = _num(m.group(1))

        by_outlet: dict[str, float] = {}
        for name in config.OUTLETS.values():
            esc = re.escape(name)
            mo = re.search(esc + r"[^0-9]{0,40}([0-9][0-9,]*\.?\d*)", text)
            if mo:
                by_outlet[name] = _num(mo.group(1))

        return {"total": total, "by_outlet": by_outlet,
                "displayed_date": displayed_date}


def _num(s: str) -> float:
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(s)) or 0)
    except ValueError:
        return 0.0
