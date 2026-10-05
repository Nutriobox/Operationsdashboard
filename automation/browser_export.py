"""
Order Summary Item CSV export — the one Petpooja step that stays in a browser.

Petpooja's order_summary_item report has no results table anymore (verified in
the SKILL, 2026-06-06): you set a date range, pick outlets, click Export, and it
queues a server-side job that later appears as a download row linking an S3 CSV.
That async "click -> wait -> file appears" flow is exactly what a browser is good
at, so we drive it with the SAME persistent profile refresh_tokens.py maintains.
Everything downstream (dedupe, addons, dashboard rebuild) is plain Python/HTTP.

Usage:
    from browser_export import export_order_csv
    path = export_order_csv("2026-08-16", out_dir, tag="1")   # -> Path to CSV

Design notes:
  - Reuses secrets/browser-profile so it inherits the logged-in Petpooja session.
    If the profile is logged out it raises SessionExpired (run refresh_tokens.py).
  - The export filter JS is a direct port of SKILL Step 2 (exclude test outlet
    399785, select all others, stamp the date into both from/to inputs).
  - We take the NEWEST download row whose text mentions target_date, then fetch
    the S3 href with the browser's own cookies via APIRequestContext, so the S3
    signature/headers are identical to a real click.
"""
from __future__ import annotations

import time
from pathlib import Path

import config
from petpooja import SessionExpired

ORDER_REPORT_URL = f"{config.PETPOOJA_BASE}/reports/order_summary_item"
PROFILE_DIR = config.SECRETS / "browser-profile"

# Direct port of SKILL Step 2 filter JS.
_SET_FILTERS_JS = """
(target) => {
  const fromEl = document.querySelector('input[name="data[Order][startdate]"]');
  const toEl   = document.querySelector('input[name="data[Order][enddate]"]');
  if (!fromEl || !toEl) return {ok:false, err:'date inputs missing'};
  fromEl.value = target; toEl.value = target;
  fromEl.dispatchEvent(new Event('change', {bubbles:true}));
  toEl.dispatchEvent(new Event('change', {bubbles:true}));
  if (typeof jQuery !== 'undefined') { jQuery(fromEl).trigger('change'); jQuery(toEl).trigger('change'); }
  const sel = document.getElementById('OrderSearchWd');
  if (!sel) return {ok:false, err:'outlet select missing'};
  const all = Array.from(sel.options).map(o=>o.value).filter(v=>v && v!=='399785');
  if (typeof jQuery !== 'undefined') jQuery(sel).val(all).trigger('change');
  else { for (const o of sel.options) o.selected = all.includes(o.value); sel.dispatchEvent(new Event('change',{bubbles:true})); }
  return {ok:true, from:fromEl.value, to:toEl.value, outlets:all.length};
}
"""

# Download href for the freshly-generated single-day report.
#
# export_order_csv always sets from == to == target, so the file we want is
# named "..._{target}_{target}.csv". The page also keeps OLDER reports around —
# notably monthly ones like "..._{target}_{month-end}.csv" — whose text also
# contains `target`. Matching on a bare `includes(target)` grabbed that stale
# monthly link, whose presigned S3 URL has long expired -> HTTP 403 (the momos /
# discount-weekly failures). Prefer the exact single-day link {target}_{target}
# first; only fall back to the looser row-text match if it's absent.
_FIND_HREF_JS = """
(target) => {
  const want = target + '_' + target;          // single-day: from==to==target
  const links = Array.from(document.querySelectorAll('a[href]'));
  for (const a of links) {                      // exact fresh report, no stale monthly
    if (/https?:/.test(a.href) && a.href.includes(want)) return a.href;
  }
  const rows = Array.from(document.querySelectorAll('tr'));
  for (const r of rows) {                      // fallback: table is newest-first
    const txt = r.textContent || '';
    if (txt.includes(target)) {
      const a = r.querySelector('a[href]');
      if (a && /https?:/.test(a.href)) return a.href;
    }
  }
  const any = document.querySelector('a[href*="amazonaws"], a[href*=".csv"]');
  return any ? any.href : null;
}
"""

_LOGIN_MARKERS = ("UserLoginForm", "data[User][password]", "/users/login")


def _is_logged_out(page) -> bool:
    try:
        html = page.content()
    except Exception:
        return False
    return any(m in html for m in _LOGIN_MARKERS)


def export_order_csv(target_date: str, out_dir: Path, tag: str = "1",
                     settle_ms: int = 12_000, headless: bool = True) -> Path:
    """
    Run one export for `target_date` (YYYY-MM-DD) and download the CSV.
    Returns the local Path. Raises SessionExpired / RuntimeError on failure.
    """
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"Order_Summary_Item_Report_{target_date}_{tag}.csv"

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            accept_downloads=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(ORDER_REPORT_URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(4_000)
            if _is_logged_out(page):
                raise SessionExpired(
                    "Petpooja is logged out in the browser profile. "
                    "Run:  python refresh_tokens.py --login"
                )

            res = page.evaluate(_SET_FILTERS_JS, target_date)
            if not res or not res.get("ok"):
                raise RuntimeError(f"could not set export filters: {res}")
            if res.get("outlets", 0) < 10:
                raise RuntimeError(f"expected 10 outlets selected, got {res.get('outlets')}")

            _click_export(page)
            page.wait_for_timeout(settle_ms)
            page.reload(wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(3_000)

            href = page.evaluate(_FIND_HREF_JS, target_date)
            if not href:
                # One more settle+reload in case the job was still queued.
                page.wait_for_timeout(settle_ms)
                page.reload(wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(3_000)
                href = page.evaluate(_FIND_HREF_JS, target_date)
            if not href:
                raise RuntimeError(
                    f"no download link appeared for {target_date}. "
                    "Export may still be processing or the page layout changed."
                )

            # Fetch the S3 file using the browser's own session/cookies.
            api = ctx.request
            resp = api.get(href, timeout=60_000)
            if not resp.ok:
                raise RuntimeError(f"S3 download failed HTTP {resp.status} for {href}")
            dest.write_bytes(resp.body())
            return dest
        finally:
            ctx.close()


# Report 31 ("Addon: Item Wise Report") builds its filter fields + data endpoint
# in JavaScript, so a plain HTTP POST is rejected (403). We drive it in the
# browser instead — a direct port of the original SKILL scrape, proven live.
_ADDON_SET_JS = """
(target) => {
  const f = document.getElementById('re_filter_filed_1_23_0_from');
  const t = document.getElementById('re_filter_filed_1_23_0_to');
  const dd = document.getElementById('re_filter_filed_1_23_3_dropdown');
  if (!f || !t) return {ok:false, err:'addon date fields (1_23) not present'};
  f.value = target; t.value = target;
  f.dispatchEvent(new Event('change', {bubbles:true}));
  t.dispatchEvent(new Event('change', {bubbles:true}));
  if (dd && typeof jQuery !== 'undefined') jQuery(dd).val('').trigger('change');
  const rid = (document.getElementById('selected_restaurant_id')||{}).value;
  return {ok:true, rid:rid};
}
"""

_ADDON_SCRAPE_JS = """
() => {
  const t = document.getElementById('re_pivot_table_1');
  if (!t) return {error:'no pivot table (re_pivot_table_1)'};
  const rows = t.querySelectorAll('tr');
  let totalRow = null, cg = '', out = [];
  rows.forEach(r => { const c = r.querySelectorAll('td');
    if (c.length >= 5 && c[0].textContent.trim() === 'Total')
      totalRow = [c[3].textContent.trim(), c[4].textContent.trim()]; });
  rows.forEach(r => { const c = r.querySelectorAll('td');
    if (c.length >= 5) {
      let ag = c[0].textContent.trim(); const ai = c[1].textContent.trim();
      const nm = c[2].textContent.trim();
      const qty = parseFloat(c[3].textContent.trim().replace(/,/g,'')) || 0;
      const tot = parseFloat(c[4].textContent.trim().replace(/,/g,'')) || 0;
      if (['Total','Min.','Max.','Avg.','Sub Total'].includes(ag)) return;
      if (ag) cg = ag;
      if (ai && nm) out.push({addonGroup: cg, addonItem: ai, qty: qty, total: tot});
    }});
  const rid = (document.getElementById('selected_restaurant_id')||{}).value;
  return {rid: rid, rows: out, pageTotal: totalRow};
}
"""

ADDON_REPORT_URL = f"{config.PETPOOJA_BASE}/custom_reports/view_report/31"


def scrape_addons(target_date: str, outlet_ids, headless: bool = True) -> dict:
    """
    Scrape the Addon Item-Wise report (view_report/31) for each outlet on
    `target_date` (YYYY-MM-DD), using the persistent Petpooja profile.

    Returns {outlet_id: [{addonGroup, addonItem, qty, total}, ...]} already
    collapsed to one row per (group, item). Verifies each outlet's summed
    qty/total against the page's own Total row and raises ScrapeError on a
    mismatch (same guard as the original). Detects stale/identical consecutive
    tables and re-searches once.
    """
    from playwright.sync_api import sync_playwright

    results: dict[int, list[dict]] = {}
    errors: dict[int, str] = {}
    prev_signature = None

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            for oid in outlet_ids:
                try:
                    rows, sig = _scrape_one_addon(ctx, page, oid, target_date)
                    if sig is not None and sig == prev_signature:
                        # identical to previous outlet -> stale table; redo once
                        rows, sig = _scrape_one_addon(ctx, page, oid, target_date, settle=2.0)
                    prev_signature = sig
                    results[oid] = rows
                except Exception as e:  # noqa: BLE001
                    errors[oid] = str(e)
                    results[oid] = []
            return {"results": results, "errors": errors}
        finally:
            ctx.close()


def _scrape_one_addon(ctx, page, oid: int, target_date: str, settle: float = 0.0):
    from petpooja import ScrapeError, SessionExpired

    # Switch the session outlet the way the UI does, then load the report.
    ctx.request.post(config.PETPOOJA_BASE + "/",
                     form={"header_changed_rest_id": str(oid)})
    page.goto(ADDON_REPORT_URL, wait_until="domcontentloaded", timeout=60_000)
    if _is_logged_out(page):
        raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")
    if settle:
        page.wait_for_timeout(int(settle * 1000))

    try:
        page.wait_for_selector("#re_filter_filed_1_23_0_from", timeout=20_000)
    except Exception:
        raise ScrapeError(
            f"addon filter fields never rendered for {config.SHORT.get(oid)} "
            "(view_report/31). Report layout may have changed.")

    res = page.evaluate(_ADDON_SET_JS, target_date)
    if not res or not res.get("ok"):
        raise ScrapeError(f"could not set addon dates for {config.SHORT.get(oid)}: {res}")
    if str(res.get("rid")) != str(oid):
        page.wait_for_timeout(1500)  # outlet switch not committed yet; one retry
        ctx.request.post(config.PETPOOJA_BASE + "/",
                         form={"header_changed_rest_id": str(oid)})
        page.goto(ADDON_REPORT_URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector("#re_filter_filed_1_23_0_from", timeout=20_000)
        page.evaluate(_ADDON_SET_JS, target_date)

    for sel in ('input[name="Search"]', 'button:has-text("Search")', '#re_search'):
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=5_000)
                break
        except Exception:
            continue
    try:
        page.wait_for_selector("#re_pivot_table_1", timeout=30_000)
    except Exception:
        # No results is legitimate (an outlet may sell no add-ons that day).
        if "No Record Found" in (page.content() or ""):
            return [], ("empty", oid)
        raise ScrapeError(f"addon results never rendered for {config.SHORT.get(oid)}")
    page.wait_for_timeout(800)

    data = page.evaluate(_ADDON_SCRAPE_JS)
    if data.get("error"):
        raise ScrapeError(f"{config.SHORT.get(oid)}: {data['error']}")

    grouped: dict[tuple, dict] = {}
    for r in data["rows"]:
        key = (r["addonGroup"], r["addonItem"])
        g = grouped.setdefault(key, {"addonGroup": r["addonGroup"],
                                     "addonItem": r["addonItem"], "qty": 0.0, "total": 0.0})
        g["qty"] += r["qty"]; g["total"] += r["total"]
    out = list(grouped.values())

    pt = data.get("pageTotal")
    if pt:
        sq = round(sum(x["qty"] for x in out))
        ss = round(sum(x["total"] for x in out))
        tq = round(float(str(pt[0]).replace(",", "") or 0))
        ts = round(float(str(pt[1]).replace(",", "") or 0))
        if sq != tq or ss != ts:
            from petpooja import ScrapeError as SE
            raise SE(f"addon sum mismatch {config.SHORT.get(oid)}: {sq}/{ss} vs page {tq}/{ts}")
    signature = (round(sum(x["qty"] for x in out)), round(sum(x["total"] for x in out)))
    return out, signature


# ---------------------------------------------------------------------------
# Captain App KOT (Captain Performance Report, view_report/27)
# ---------------------------------------------------------------------------
# Petpooja changed this report (verified 2026-08-24): the filter inputs and the
# results are now built in JavaScript, so the old pure-HTTP scrape (petpooja.py
# ::captain_kots) gets a bare page with no re_filter_filed_* inputs, and the
# get_data_query/1/19 endpoint returns 403 when POSTed directly. So we drive it
# in the browser with the SAME persistent profile as the addon/export scrapes.
#
# Read = the "No of Kots" cell (3rd column) on the report's Total row. The pivot
# fills incrementally (a partial number then the final one), so we poll until the
# value stops changing before trusting it.
CAPTAIN_REPORT_URL = f"{config.PETPOOJA_BASE}/custom_reports/view_report/27"

_CAPTAIN_SET_JS = """
([f, t]) => {
  const a = document.getElementById('re_filter_filed_1_19_0_from');
  const b = document.getElementById('re_filter_filed_1_19_0_to');
  if (!a || !b) return {ok:false, err:'captain date fields (1_19) not present'};
  a.removeAttribute('readonly'); b.removeAttribute('readonly');
  a.value = f; b.value = t;
  a.dispatchEvent(new Event('change', {bubbles:true}));
  b.dispatchEvent(new Event('change', {bubbles:true}));
  const s = document.getElementById('selected_from_date');
  const e = document.getElementById('selected_end_date');
  if (s) s.value = f; if (e) e.value = t;
  const rid = (document.getElementById('selected_restaurant_id')||{}).value;
  return {ok:true, from:a.value, to:b.value, rid:rid};
}
"""

# Return the Total row's "No of Kots" as a number, or the sentinels
# 'NO_RECORD' / 'PENDING' so the poller knows what it's looking at.
_CAPTAIN_READ_JS = """
() => {
  const body = document.body.innerText || '';
  const t = document.getElementById('re_pivot_table_1');
  if (t) {
    const rows = t.querySelectorAll('tr');
    for (const r of rows) {
      const c = r.querySelectorAll('td');
      if (c.length >= 3 && c[0].textContent.trim() === 'Total') {
        const raw = c[2].textContent.trim().replace(/,/g, '');
        const n = parseFloat(raw);
        return isNaN(n) ? 'PENDING' : n;
      }
    }
  }
  if (/No Record Found/i.test(body)) return 'NO_RECORD';
  return 'PENDING';
}
"""


def _captain_one(ctx, page, oid: int, from_dt: str, to_dt: str) -> int:
    """Scrape one outlet's Captain-App KOT total for [from_dt, to_dt)."""
    from petpooja import ScrapeError, SessionExpired

    # Switch the session outlet the way the UI's hidden form does — a synchronous
    # server-side POST (same mechanism the addon scraper uses). change_restaurant()
    # JS is async and races the read, so an outlet occasionally loaded showing the
    # PREVIOUS outlet's id. On this shared live account the switch can also fail to
    # commit before the report loads, which redirects to the reports-list page
    # (no filter fields). Both are the same collision, so retry the whole
    # switch+load: re-POST the switch, reload the report, and require both the
    # filter fields AND the right outlet id before proceeding.
    # NOTE (2026-08-27): the outlet-switch POST and the report navigation are the
    # first network calls of each attempt, and Petpooja resets the connection on
    # them fairly often — 2 of 3 validation runs died here with
    # "APIRequestContext.post: read ECONNRESET". Previously those raised straight
    # out of this loop, so a transport blip failed the entire job. They are now
    # retryable like any other collision: same loop, same backoff.
    last_rid, last_err = None, None
    for attempt in range(4):
        try:
            ctx.request.post(config.PETPOOJA_BASE + "/",
                             form={"header_changed_rest_id": str(oid)})
            page.goto(CAPTAIN_REPORT_URL, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            msg = str(e).split("\n")[0]
            if isinstance(e, SessionExpired):
                raise
            last_err = f"transport error on switch/navigate: {msg}"
            page.wait_for_timeout(2_000 * (attempt + 1))
            continue
        if _is_logged_out(page):
            raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")
        try:
            page.wait_for_selector("#re_filter_filed_1_19_0_from", timeout=20_000)
        except Exception:
            last_err = "filter fields never rendered (switch likely uncommitted)"
            page.wait_for_timeout(1_500 * (attempt + 1))
            continue
        page.wait_for_timeout(1_200)
        last_rid = page.evaluate(
            "() => {const e=document.getElementById('selected_restaurant_id');return e?e.value:'';}")
        if str(last_rid) == str(oid):
            break
        last_err = f"page shows outlet {last_rid}"
        page.wait_for_timeout(1_500 * (attempt + 1))  # switch not committed; settle
    else:
        raise ScrapeError(
            f"outlet switch to {config.SHORT.get(oid)} never settled ({last_err})")

    res = page.evaluate(_CAPTAIN_SET_JS, [from_dt, to_dt])
    if not res or not res.get("ok"):
        raise ScrapeError(f"could not set captain dates for {config.SHORT.get(oid)}: {res}")
    if str(res.get("rid")) != str(oid):
        raise ScrapeError(
            f"captain report outlet mismatch for {config.SHORT.get(oid)}: "
            f"page shows {res.get('rid')}")

    page.click("input.re_final_search", timeout=15_000)

    # Poll until the Total row's value is present and stable across two reads.
    last, stable = None, 0
    for _ in range(30):
        page.wait_for_timeout(1_500)
        v = page.evaluate(_CAPTAIN_READ_JS)
        if v == "NO_RECORD":
            return 0
        if v == "PENDING":
            stable = 0
            continue
        if v == last:
            stable += 1
            if stable >= 2:
                return int(round(float(v)))
        else:
            last, stable = v, 0
    if last is not None:
        return int(round(float(last)))
    raise ScrapeError(f"captain result never settled for {config.SHORT.get(oid)}")


def scrape_captain_kots(from_dt: str, to_dt: str, outlet_ids,
                        headless: bool = True, cookie: str | None = None) -> dict:
    """
    Captain-App KOT totals for every outlet in `outlet_ids` over one window.

    from_dt/to_dt use Petpooja's report format, e.g. "2026-08-23 01:00:00".
    Returns {"results": {oid: int}, "errors": {oid: str}}.

    Production drives the persistent profile refresh_tokens.py keeps signed in
    (cookie=None). Passing an explicit `cookie` (the Netscape-style string from
    tokens.json) uses a throwaway context instead — handy for testing off the
    laptop without touching the real profile.
    """
    import json
    from playwright.sync_api import sync_playwright

    # Default to the persistent browser profile (cookie=""). Petpooja's report
    # pages are now per-outlet gated: a cookie-only throwaway session reverts to
    # "All Outlets" (selected_restaurant_id = 0), so view_report/27 renders no
    # filter fields and every outlet switch "never settles" (verified 2026-09-05).
    # The profile — signed in via refresh_tokens.py --login — commits single-outlet
    # switches, exactly as the KOT reader now relies on. Pass an explicit cookie
    # string to force the old throwaway-context behaviour.
    if cookie is None:
        cookie = ""

    results, errors = {}, {}
    with sync_playwright() as p:
        if cookie:
            browser = p.chromium.launch(headless=headless,
                                        args=["--disable-blink-features=AutomationControlled"])
            ctx = browser.new_context()
            ctx.add_cookies([
                {"name": n.strip(), "value": v.strip(),
                 "domain": "billing.petpooja.com", "path": "/"}
                for n, v in (kv.split("=", 1) for kv in cookie.split(";") if "=" in kv)
            ])
            closer = browser
        else:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR), headless=headless,
                args=["--disable-blink-features=AutomationControlled"])
            closer = ctx
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            # Leave "All Outlets" mode so the per-outlet report will render. A plain
            # switch + dashboard load is NOT enough — the session only commits to
            # single-outlet mode after an in-app navigation. Reuse the KOT prime
            # (dashboard -> click KOT), which is proven to commit the switch; after
            # it, per-outlet switches for view_report/27 settle.
            try:
                _prime_kot_page(page, ctx, outlet_ids[0])
            except Exception:
                pass  # the per-outlet switch below retries anyway
            for oid in outlet_ids:
                try:
                    results[oid] = _captain_one(ctx, page, oid, from_dt, to_dt)
                    print(f"    Captain {config.SHORT.get(oid, oid):<16} = {results[oid]}",
                          flush=True)
                except Exception as e:  # noqa: BLE001
                    errors[oid] = str(e)
                    print(f"    Captain {config.SHORT.get(oid, oid):<16} FAILED: "
                          f"{str(e).splitlines()[0]}", flush=True)
            return {"results": results, "errors": errors}
        finally:
            closer.close()


# ---------------------------------------------------------------------------
# Total KOT (Dine In + Pick Up) — the KOT list at /items/kot_list/
# ---------------------------------------------------------------------------
# Petpooja changed this (verified live 2026-09-05): the KOT list is now a
# single-page-app route. A direct GET/POST to /items/kot_list/ returns a
# <script>window.location='/users/dashboard'</script> stub, so the server-side
# page context the results endpoint needs is never set and /items/klist/ answers
# with the one-byte sentinel "9" (the old pure-HTTP petpooja.py::kot_count path).
#
# The list only renders when reached from inside the loaded app (Dashboard ->
# sidebar "KOT"). Once that in-app navigation has primed the session, the same
# /items/klist/ POST returns the real table ("Showing 1 to X of N records") for
# WHICHEVER outlet is the session's current outlet. So we:
#   1. load the dashboard in the persistent profile, click the sidebar KOT link
#      once (prime), and wait for the KOT filter form (#KotStartdate),
#   2. per outlet: switch the session outlet (the hidden #change_res form), then
#      POST /items/klist/ from inside the page with order_type = Pick Up + Dine In
#      and read "of N records".
# Verified 2026-09-05: DLF Phase 2 -> 32, Rajinder Nagar -> 45 for 4 Sep, which
# matches Petpooja's own on-screen count for [Pick Up, Dine In].
KOT_LIST_URL = f"{config.PETPOOJA_BASE}/items/kot_list/"
DASHBOARD_URL = f"{config.PETPOOJA_BASE}/users/dashboard"

# Runs inside the primed KOT page. Switches nothing — the caller has already
# switched the session outlet — just queries klist and parses the record count.
_KLIST_COUNT_JS = r"""
async ([oid, start, end, pickup, dinein]) => {
  const b = new URLSearchParams();
  const put = (k, v) => b.append(k, v);
  put('data[Kot][startdate]', start);
  put('data[Kot][enddate]', end);
  put('data[Kot][order_type]', '');
  put('data[Kot][kot_id]', '');
  put('data[Kot][customer_name]', '');
  put('data[Kot][customer_phone]', '');
  put('data[Kot][table_no]', '');
  put('data[restaurant_id]', String(oid));
  put('data[current_page_url]', location.origin + '/items/kot_list/');
  put('data[Kot][order_type][]', pickup);   // Pick Up
  put('data[Kot][order_type][]', dinein);   // Dine In
  let resp;
  try {
    resp = await fetch(location.origin + '/items/klist/', {
      method: 'POST', credentials: 'include',
      headers: {'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
      body: b.toString(),
    });
  } catch (e) { return {ok:false, err:'fetch failed: ' + e}; }
  const t = await resp.text();
  if (t.trim() === '9') return {ok:false, sentinel:true};
  if (/UserLoginForm|\/users\/login/.test(t)) return {ok:false, loggedOut:true};
  if (/No Results Found/i.test(t)) return {ok:true, count:0};
  const m = t.match(/of\s+([0-9,]+)\s+records/i);
  if (!m) return {ok:false, err:'no "of N records" (len ' + t.length + ')'};
  return {ok:true, count: parseInt(m[1].replace(/,/g, ''), 10)};
}
"""


def _prime_kot_page(page, ctx, prime_oid):
    """
    Open the KOT list so klist stops sentinelling. Verified live (2026-09-05):

    - A DIRECT hit to /items/kot_list/ never works from a clean session — the
      server serves a <script>window.location='/users/dashboard'</script> stub and
      the browser lands on the dashboard.
    - The KOT list is a per-outlet feature: on "All Outlets" (the default) the
      sidebar has NO "KOT" item, so it can't be reached. We must first switch the
      session to a SINGLE outlet (the hidden #change_res form), then the dashboard
      renders the KOT sidebar link, and clicking it opens the list AND primes klist
      for every outlet thereafter.

    So we replicate the human flow: switch to one outlet, load the dashboard, wait
    for the KOT menu link, click it, wait for the KOT filter form.
    """
    from petpooja import ScrapeError, SessionExpired

    # 1) leave "All Outlets" — select a single outlet so the KOT menu appears
    try:
        ctx.request.post(config.PETPOOJA_BASE + "/",
                         form={"header_changed_rest_id": str(prime_oid)})
    except Exception:
        pass  # transport blip; the dashboard load below will still carry the switch

    def _goto(url):
        last = None
        for attempt in range(4):  # Petpooja resets connections fairly often
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                return
            except Exception as e:
                last = str(e).splitlines()[0]
                page.wait_for_timeout(2_000 * (attempt + 1))
        raise ScrapeError(f"could not load {url} (transport): {last}")

    _goto(DASHBOARD_URL)
    page.wait_for_timeout(2_500)   # the dashboard may serve a one-shot reload stub
    if _is_logged_out(page):
        raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")

    # Wait for the full dashboard (its KOT sidebar link), then navigate in-app.
    try:
        page.wait_for_selector('a[href*="kot_list"]', timeout=25_000)
    except Exception:
        raise ScrapeError(
            f"dashboard did not fully render (no KOT menu link; at {page.url!r}) — "
            "the automation profile may need: python refresh_tokens.py --login")
    # Dismiss the one-shot "Today's Snapshot" dashboard modal if it's up — it
    # overlays the sidebar and intercepts the KOT-link click, which surfaced as
    # the "could not click the KOT menu link" Page.click timeout. Added 2026-10-05.
    for _sel in ('button:has-text("Skip")', 'text=Skip', '[aria-label="Close"]'):
        try:
            page.click(_sel, timeout=1_500)
            break
        except Exception:
            pass
    # Open the KOT list. Try the sidebar-link click first (the human flow); if it
    # is still intercepted, navigate straight to it. The KOT link already rendered,
    # which proves the single-outlet switch committed, so a direct goto now serves
    # the real page — not the dashboard reload stub a clean (un-switched) session
    # gets. Verified live 2026-10-05.
    opened = False
    try:
        page.click('a[href*="kot_list"]', timeout=8_000)
        opened = True
    except Exception:
        pass
    if not opened:
        try:
            page.goto(KOT_LIST_URL, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            raise ScrapeError(f"could not open the KOT list: {str(e).splitlines()[0]}")
    try:
        page.wait_for_selector("#KotStartdate", timeout=25_000)
    except Exception:
        # Last resort: one more direct navigation now that the outlet is committed.
        try:
            page.goto(KOT_LIST_URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_selector("#KotStartdate", timeout=20_000)
        except Exception:
            raise ScrapeError(
                f"KOT list did not render (at {page.url!r}) — "
                "Petpooja may have changed the KOT page")


def scrape_kot_totals(kot_from: str, kot_to: str, outlet_ids,
                      headless: bool = True, cookie: str | None = None) -> dict:
    """
    Total (Dine In + Pick Up) KOT counts for every outlet over one window.

    kot_from/kot_to use Petpooja's KOT format, e.g. "4 Sep 2026 01:00:00".
    Returns {"results": {oid: int}, "errors": {oid: str}} — same shape as
    scrape_captain_kots, so callers treat the two identically.

    Defaults to the persistent browser-profile refresh_tokens.py keeps signed in
    (cookie=None) because priming needs the full dashboard SPA to render the KOT
    sidebar link. Pass an explicit cookie string to use a throwaway context
    (handy for testing), or cookie="" to force the persistent profile.
    """
    import json
    from playwright.sync_api import sync_playwright
    from petpooja import ScrapeError, SessionExpired

    pickup, dinein = config.ORDER_TYPE_PICKUP, config.ORDER_TYPE_DINEIN

    # Which session(s) to try, in order. The persistent profile renders the full
    # dashboard SPA (so the KOT sidebar link is present), but its Petpooja login
    # can rot; the tokens.json cookie is always the fresh session but a throwaway
    # context may render a lighter dashboard. Trying profile then cookie makes the
    # reader robust to either being the healthy one.
    if cookie:                       # explicit cookie override
        modes = [("cookie", cookie)]
    elif cookie == "":               # explicit profile override
        modes = [("profile", None)]
    else:                            # auto: profile first, then the fresh cookie
        try:
            tok_cookie = json.loads(config.TOKENS_FILE.read_text())["petpooja_cookie"]
        except Exception:
            tok_cookie = ""
        modes = [("profile", None)] + ([("cookie", tok_cookie)] if tok_cookie else [])

    def _launch(p, mode, ck):
        if mode == "cookie":
            browser = p.chromium.launch(
                headless=headless, args=["--disable-blink-features=AutomationControlled"])
            ctx = browser.new_context()
            ctx.add_cookies([
                {"name": n.strip(), "value": v.strip(),
                 "domain": "billing.petpooja.com", "path": "/"}
                for n, v in (kv.split("=", 1) for kv in ck.split(";") if "=" in kv)])
            return ctx, browser
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"])
        return ctx, ctx

    def _pull(ctx, page):
        results, errors = {}, {}
        for oid in outlet_ids:
            last_err = None
            for attempt in range(4):
                try:
                    ctx.request.post(config.PETPOOJA_BASE + "/",
                                     form={"header_changed_rest_id": str(oid)})
                except Exception as e:  # transport blip — retry
                    last_err = f"switch transport error: {str(e).splitlines()[0]}"
                    page.wait_for_timeout(1_500 * (attempt + 1))
                    continue
                page.wait_for_timeout(1_000 + 400 * attempt)  # let the switch commit
                res = page.evaluate(_KLIST_COUNT_JS,
                                    [oid, kot_from, kot_to, pickup, dinein])
                if res.get("loggedOut"):
                    raise SessionExpired(
                        "Petpooja logged out — run refresh_tokens.py --login")
                if res.get("ok"):
                    results[oid] = int(res["count"])
                    print(f"    KOT   {config.SHORT.get(oid, oid):<18} = {res['count']}",
                          flush=True)
                    break
                last_err = "klist sentinel '9' (switch uncommitted)" \
                    if res.get("sentinel") else res.get("err", "unknown")
                page.wait_for_timeout(1_500 * (attempt + 1))
            else:
                errors[oid] = last_err or "failed"
                print(f"    KOT   {config.SHORT.get(oid, oid):<18} FAILED: {last_err}",
                      flush=True)
        return {"results": results, "errors": errors}

    prime_err = None
    with sync_playwright() as p:
        for i, (mode, ck) in enumerate(modes):
            ctx, closer = _launch(p, mode, ck)
            try:
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                try:
                    _prime_kot_page(page, ctx, outlet_ids[0])   # once for the whole session
                except (ScrapeError, SessionExpired) as e:
                    prime_err = f"[{mode}] {e}"
                    if i + 1 < len(modes):
                        continue            # try the next session mode
                    raise ScrapeError(f"could not open KOT list ({prime_err})")
                return _pull(ctx, page)
            finally:
                closer.close()


def browser_custom_report(view_id: int, outlet_id: int, from_dt: str, to_dt: str,
                          headless: bool = True) -> str:
    """
    Read a Petpooja custom report through the primed single-outlet browser session.

    The pure-HTTP path (petpooja.custom_report) is gated/unreliable from the laptop,
    and Petpooja builds the report's filter inputs in JavaScript (they're only in the
    live DOM, not the fetched HTML). So we navigate to view_report/{id} in the primed
    single-outlet session (exactly like the working Captain scraper), set the date
    range in the DOM, click Search, wait for the results table, and return the
    rendered page HTML. Parse it with the caller's BeautifulSoup logic.
    from_dt/to_dt use the report format "2026-08-24 00:00:00".
    """
    from playwright.sync_api import sync_playwright
    from petpooja import ScrapeError, SessionExpired
    base = config.PETPOOJA_BASE
    url = f"{base}/custom_reports/view_report/{view_id}"

    _SET_DATES = """
    ([f, t]) => {
      let n = 0;
      document.querySelectorAll('input[id^="re_filter_filed_"]').forEach(el => {
        if (/_from$/.test(el.id)) { el.removeAttribute('readonly'); el.value = f;
          el.dispatchEvent(new Event('change', {bubbles:true})); n++; }
        if (/_to$/.test(el.id))   { el.removeAttribute('readonly'); el.value = t;
          el.dispatchEvent(new Event('change', {bubbles:true})); n++; }
      });
      const s = document.getElementById('selected_from_date');
      const e = document.getElementById('selected_end_date');
      if (s) s.value = f; if (e) e.value = t;
      return n;
    }
    """

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            _prime_kot_page(page, ctx, outlet_id)      # commit single-outlet mode

            last = None
            for attempt in range(4):
                try:
                    ctx.request.post(base + "/", form={"header_changed_rest_id": str(outlet_id)})
                    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                except Exception as e:
                    last = f"transport: {str(e).splitlines()[0]}"
                    page.wait_for_timeout(2_000 * (attempt + 1)); continue
                if _is_logged_out(page):
                    raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")
                try:
                    page.wait_for_selector('[id^="re_filter_filed_"]', timeout=20_000)
                    break
                except Exception:
                    last = "filter fields never rendered (switch uncommitted?)"
                    page.wait_for_timeout(1_500 * (attempt + 1))
            else:
                raise ScrapeError(f"view_report/{view_id}: {last}")

            if not page.evaluate(_SET_DATES, [from_dt, to_dt]):
                raise ScrapeError(f"view_report/{view_id}: no _from/_to date inputs in DOM")

            # click the report's Search/apply control
            for sel in ("input.re_final_search", "button.re_final_search", "#re_search",
                        'button:has-text("Search")', 'input[type=submit][value*="Search"]',
                        'input[type=button][value*="Search"]'):
                try:
                    loc = page.locator(sel)
                    if loc.count():
                        loc.first.click(timeout=8_000); break
                except Exception:
                    continue

            # Wait for the results TABLE (a table whose header has "Total Sales" and
            # that lists outlet rows) and for its row count to stop growing — the
            # report fills incrementally, so a fixed sleep can read a partial table
            # (that's what dropped an outlet / found "no table").
            _COUNT_JS = """
            () => {
              const SKIP = ['total','min.','max.','avg.','sub total',''];
              for (const tb of document.querySelectorAll('table')) {
                const hs = [...tb.querySelectorAll('th')].map(th => (th.textContent||'').toLowerCase());
                if (!hs.some(h => /total\\s*sales/.test(h) && !/net/.test(h))) continue;
                let rows = 0;
                for (const tr of tb.querySelectorAll('tr')) {
                  const td = tr.querySelector('td');
                  if (!td) continue;
                  const first = (td.textContent||'').trim().toLowerCase();
                  if (!SKIP.includes(first)) rows++;   // a real outlet data row
                }
                return rows;
              }
              return -1;   // no results table yet
            }
            """
            last, stable = -1, 0
            for _ in range(40):                      # up to ~60s
                page.wait_for_timeout(1_500)
                try:
                    n = page.evaluate(_COUNT_JS)
                except Exception:
                    n = -1
                if n > 0 and n == last:
                    stable += 1
                    if stable >= 2:                  # data rows present & steady
                        break
                else:
                    last, stable = n, 0
            page.wait_for_timeout(800)
            return page.content()
        finally:
            ctx.close()


def fetch_restaurant_sales(from_date: str, to_date: str,
                           headless: bool = True) -> dict:
    """
    All-outlet Total Sales for [from_date, to_date] (YYYY-MM-DD) from the dashboard's
    own JSON endpoint (/users/load_restaurants_wise_data/), fetched IN-PAGE so it uses
    the logged-in session (reliable from the laptop, unlike raw HTTP). This is the
    "All Outlets" view — no single-outlet priming needed.

    Returns {"total": float|None, "by_res": {res_id(int): total_sales(float)}}.
    """
    import json as _json
    from playwright.sync_api import sync_playwright
    from petpooja import ScrapeError, SessionExpired
    base = config.PETPOOJA_BASE

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            last = None
            for attempt in range(4):
                try:
                    page.goto(f"{base}/users/dashboard", wait_until="domcontentloaded",
                              timeout=60_000)
                    break
                except Exception as e:
                    last = str(e).splitlines()[0]
                    page.wait_for_timeout(2_000 * (attempt + 1))
            else:
                raise ScrapeError(f"could not load dashboard (transport): {last}")
            page.wait_for_timeout(2_500)
            if _is_logged_out(page):
                raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")

            raw = ""
            for attempt in range(4):
                raw = page.evaluate(
                    "async ({f, t}) => {"
                    " const r = await fetch('/users/load_restaurants_wise_data/', {"
                    "   method:'POST', credentials:'include',"
                    "   headers:{'Content-Type':'application/x-www-form-urlencoded',"
                    "   'X-Requested-With':'XMLHttpRequest'},"
                    "   body: 'from_date=' + f + '&to_date=' + t});"
                    " return await r.text(); }",
                    {"f": from_date, "t": to_date})
                if raw and raw.lstrip().startswith("{"):
                    break
                page.wait_for_timeout(1_500 * (attempt + 1))
            try:
                data = _json.loads(raw)
            except Exception:
                raise ScrapeError(
                    f"load_restaurants_wise_data did not return JSON (len={len(raw)})")

            arr = data.get("all_restaurant_statistics") or []
            total, by_res = None, {}
            for e in arr:
                rid = e.get("res_id")
                ts = e.get("total_sales")
                try:
                    ts = float(ts)
                except (TypeError, ValueError):
                    continue
                name = (e.get("res_name") or e.get("name") or "").strip().lower()
                if rid in (0, None) or name == "total":
                    total = ts
                else:
                    by_res[int(rid)] = ts
            if not by_res:
                raise ScrapeError("load_restaurants_wise_data: no per-outlet rows parsed")
            return {"total": total, "by_res": by_res}
        finally:
            ctx.close()


def _click_export(page) -> None:
    """Click whatever the Export control is; id contains 'order_searc' or text 'Export'."""
    for sel in ('button:has-text("Export")', 'a:has-text("Export")',
                'input[type="button"][value*="Export"]',
                '[id*="order_searc"]', '#order_searc1h'):
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=5_000)
                return
        except Exception:
            continue
    # Last resort: submit the report form.
    try:
        page.evaluate("() => { const f=document.querySelector('form'); if (f) f.submit(); }")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"could not find/click the Export control: {e}")


if __name__ == "__main__":
    import sys
    from datetime import datetime, timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    d = sys.argv[1] if len(sys.argv) > 1 else (
        (datetime.now(ist).date() - timedelta(days=1)).strftime("%Y-%m-%d"))
    out = config.ROOT / "outputs"
    print("Exporting", d, "->", out)
    print("Saved:", export_order_csv(d, out, headless="--headed" not in sys.argv))
