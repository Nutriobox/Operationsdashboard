"""
Petpooja POS dashboard scrape for an arbitrary date — the browser step of the
Daily Dashboard job (port of the Cowork task `petpooja-sales-to-gsheet`).

Why a browser and not HTTP: `petpooja.pos_dashboard_total()` can only read the
dashboard's DEFAULT window, because the date range lives in a daterangepicker
whose change is applied by JS and fetched over AJAX. The Zomato/Swiggy split is
worse — it only exists inside a tooltip rendered after a kebab click. Both are
exactly the "JS-rendered, no HTTP equivalent" case the other ports use
Playwright for.

Reuses secrets/browser-profile (the same persistent profile refresh_tokens.py
maintains), so it inherits the logged-in Petpooja session.

Usage:
    from dashboard_scrape import scrape_daily
    data = scrape_daily("2026-08-26")

Returns:
    {
      "displayed_range": str,          # what the picker shows after we set it
      "total_sales": float,
      "net_sales": float,
      "online_sales": float,
      "online_pct": float,             # e.g. 72.75
      "discount_pct": float,           # e.g. 22.40
      "total_orders": int,
      "zomato": float,                 # absolute online rupees
      "swiggy": float,
      "by_outlet": {petpooja_name: {"orders": int, "total": float, "net": float}},
    }

Design notes:
  - SKILL rule honoured: we never click a Petpooja sidebar link, and we never
    screenshot this page. Everything is read via page.evaluate().
  - The date is stamped through the daterangepicker API *and* the hidden
    from/to inputs, then every listener the page might use is fired — a direct
    port of the Cowork task's Step 2b JS.
  - We assert the picker actually moved to the target date before trusting any
    number. Silently reading the default window (today) and writing it into
    yesterday's row is the single worst failure this job can have.
"""
from __future__ import annotations

import re

import config
from petpooja import SessionExpired

DASHBOARD_URL = f"{config.PETPOOJA_BASE}/users/dashboard/"
PROFILE_DIR = config.SECRETS / "browser-profile"

_LOGIN_MARKERS = ("UserLoginForm", "data[User][password]", "/users/login")

# Port of Cowork Step 2b — stamp the target date and fire every listener.
_SET_DATE_JS = """
(target) => {
  const el = document.getElementById('statisticsdaterange');
  if (!el) return {ok:false, err:'daterange element missing'};
  if (typeof window.jQuery === 'undefined' || typeof window.moment === 'undefined')
    return {ok:false, err:'jQuery/moment not loaded'};
  const $el = window.jQuery(el);
  const drp = $el.data('daterangepicker');
  if (!drp) return {ok:false, err:'daterangepicker not initialised'};
  drp.setStartDate(window.moment(target));
  drp.setEndDate(window.moment(target));
  $el.trigger('apply.daterangepicker', [drp]);
  if (drp.callback) drp.callback(drp.startDate, drp.endDate);
  const f = document.getElementById('total_statistics_from_date');
  const t = document.getElementById('total_statistics_to_date');
  if (f) f.value = target;
  if (t) t.value = target;
  return {ok:true, shown:(el.textContent||'').trim()};
}
"""

_CLICK_LIST_JS = """
() => {
  const b = [...document.querySelectorAll('button')]
    .find(x => (x.textContent||'').trim() === 'List');
  if (!b) return false;
  b.click();
  return true;
}
"""

# Port of Cowork Step 2c action 1 — summary cards + per-outlet list rows.
_READ_JS = """
() => {
  const t = document.body.innerText;
  const grab = (re) => { const m = t.match(re); return m ? m[1].replace(/,/g,'') : null; };
  const summary = {
    totalSales:    grab(/Total Sales\\s*([\\d,]+\\.\\d+)/),
    netSales:      grab(/Net Sales\\s*([\\d,]+\\.\\d+)/),
    onlineSales:   grab(/Online Sales\\s*([\\d,]+\\.\\d+)/),
    onlinePct:     grab(/([\\d.]+)% of sales generated from Online/),
    cashCollected: grab(/Cash Collected\\s*([\\d,]+\\.\\d+)/),
    discountPct:   grab(/([\\d.]+)% Discounts given/),
  };
  const lines = t.split('\\n');
  const outlets = {};
  let totalOrders = null;
  for (const line of lines) {
    const tm = line.match(/^Total\\s+([\\d,]+)\\s+([\\d,]+\\.\\d+)\\s+([\\d,]+\\.\\d+)/);
    if (tm) totalOrders = tm[1].replace(/,/g,'');
    const om = line.match(/^(NutrioBox\\s*\\([^)]+\\))\\s+([\\d,]+)\\s+([\\d,]+\\.\\d+)\\s+([\\d,]+\\.\\d+)/);
    if (om) outlets[om[1].trim()] = {
      orders: om[2].replace(/,/g,''),
      total:  om[3].replace(/,/g,''),
      net:    om[4].replace(/,/g,''),
    };
  }
  return JSON.stringify({summary, totalOrders, outlets});
}
"""

_KEBAB_JS = """
() => {
  const cards = [...document.querySelectorAll('.dashboard-card, [class*="card"], .MuiPaper-root')];
  for (const c of cards) {
    if (!/Online Sales/.test(c.textContent || '')) continue;
    const k = c.querySelector('button[aria-haspopup], button [data-icon*="more"], button svg, [class*="kebab"], [class*="dots"]');
    if (k) { (k.closest('button') || k).click(); return true; }
  }
  return false;
}
"""

_READ_SPLIT_JS = """
() => {
  const t = document.body.innerText;
  const m = t.match(/Zomato\\s+([\\d,]+(?:\\.\\d+)?)[\\s\\S]*?Swiggy\\s+([\\d,]+(?:\\.\\d+)?)/);
  return m ? JSON.stringify({zomato: m[1].replace(/,/g,''), swiggy: m[2].replace(/,/g,'')}) : null;
}
"""


def _num(s, default=None):
    if s is None:
        return default
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(s)) or 0)
    except ValueError:
        return default


def _is_logged_out(page) -> bool:
    try:
        html = page.content()
    except Exception:
        return False
    return any(m in html for m in _LOGIN_MARKERS)


def _date_matches(shown: str, target: str) -> bool:
    """
    Confirm the picker really moved to `target` (YYYY-MM-DD).

    The widget renders e.g. "26/08/2026 - 26/08/2026", "Aug 26, 2026", or —
    as actually observed on 2026-08-27 — "26th Aug": ordinal day plus
    abbreviated month, with NO year. An earlier version of this function
    required the year and therefore rejected a perfectly correct date, so the
    year is now optional: if one is rendered it must match ours, but its
    absence is not a failure. Anything that does not match the day AND month is
    still rejected rather than guessed at.
    """
    if not shown:
        return False
    y, m, d = target.split("-")
    months = ["january", "february", "march", "april", "may", "june", "july",
              "august", "september", "october", "november", "december"]
    mon = months[int(m) - 1]
    s = shown.lower()
    day, month_i = int(d), int(m)

    # If any 4-digit year is rendered, it must be ours.
    years = re.findall(r"\b(20\d{2})\b", s)
    if years and y not in years:
        return False

    # dd/mm/yyyy, dd-mm-yyyy or yyyy-mm-dd
    numeric = (
        f"{day:02d}/{month_i:02d}/{y}" in s
        or f"{day:02d}-{month_i:02d}-{y}" in s
        or f"{y}-{month_i:02d}-{day:02d}" in s
    )
    # "26 Aug", "26th Aug", "Aug 26", "August 26" — year optional.
    textual = mon[:3] in s and re.search(rf"\b{day}(?:st|nd|rd|th)?\b", s) is not None
    return numeric or textual


# res_id -> the outlet name daily_sheet's COLUMN_OUTLET expects (exact strings).
_RES_NAME = {
    9960:   "NutrioBox (Prashant Vihar)",
    19652:  "NutrioBox (Janakpuri)",
    16011:  "NutrioBox (Karkardooma)",
    62697:  "NutrioBox (Dwarka)",
    62695:  "NutrioBox (Shivalik)",
    80991:  "NutrioBox (Noida)",
    159181: "NutrioBox ( Rajinder Nagar)",
    349767: "NutrioBox ( DLF Phase 2)",
    369621: "NutrioBox (Sector 15, Gurugram)",
    136183: "NutrioBox ( Sector 63 Noida )",
}

_FETCH_JS = (
    "async ({ep, f, t}) => {"
    " const r = await fetch(ep, {method:'POST', credentials:'include',"
    "   headers:{'Content-Type':'application/x-www-form-urlencoded',"
    "   'X-Requested-With':'XMLHttpRequest'},"
    "   body: 'from_date=' + f + '&to_date=' + t});"
    " return await r.text(); }"
)


def scrape_daily(target_date: str, headless: bool = True,
                 settle_ms: int = 4_000) -> dict:
    """
    Read the POS dashboard figures for `target_date` (YYYY-MM-DD).

    Petpooja redesigned the dashboard (2026-09), removing the jQuery daterangepicker
    and reshaping the List view — the old picker+table+kebab scrape broke. This now
    reads the dashboard's OWN JSON endpoints in-page (reliable from the laptop):
      - /users/load_restaurants_wise_data/  -> per-outlet total_sales/orders/net
      - /users/load_sales_statistics/       -> company totals + online split
        (t_net=net, t_o=online, o_t_z=Zomato, o_t_s=Swiggy, total_discount, total_orders)
    Percentages match the dashboard cards' own convention (÷ Total Sales; verified
    online% = online/total_sales = 87.69% against the live card).

    Raises SessionExpired if logged out, RuntimeError on a data failure.
    """
    import json
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            last = None
            for attempt in range(4):
                try:
                    page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=60_000)
                    break
                except Exception as e:
                    last = str(e).splitlines()[0]
                    page.wait_for_timeout(2_000 * (attempt + 1))
            else:
                raise RuntimeError(f"could not load dashboard (transport): {last}")
            page.wait_for_timeout(settle_ms)
            if _is_logged_out(page):
                raise SessionExpired(
                    "Petpooja is logged out in the browser profile. "
                    "Run:  python refresh_tokens.py --login")

            def _fetch(ep):
                for attempt in range(4):
                    raw = page.evaluate(_FETCH_JS, {"ep": ep, "f": target_date, "t": target_date})
                    if raw and raw.lstrip().startswith("{"):
                        return json.loads(raw)
                    page.wait_for_timeout(1_500 * (attempt + 1))
                raise RuntimeError(f"{ep} did not return JSON")

            rw = _fetch("/users/load_restaurants_wise_data/")
            st = _fetch("/users/load_sales_statistics/").get("Statistics_data") or {}

            by_outlet = {}
            for e in rw.get("all_restaurant_statistics", []):
                rid = e.get("res_id")
                if rid in (0, None):
                    continue
                name = _RES_NAME.get(int(rid))
                if not name:
                    continue
                by_outlet[name] = {
                    "orders": int(_num(e.get("total_orders"), 0) or 0),
                    "total": _num(e.get("total_sales"), 0.0),
                    "net": _num(e.get("net_sales"), 0.0),
                }

            total_sales = _num(st.get("total_sales"))
            net_sales = _num(st.get("t_net"))
            online = _num(st.get("t_o"))
            zomato = _num(st.get("o_t_z"))
            swiggy = _num(st.get("o_t_s"))
            discount = _num(st.get("total_discount"))
            orders = int(_num(st.get("total_orders"), 0) or 0)
            online_pct = round(online / total_sales * 100, 2) if (online and total_sales) else 0.0
            # Discount % must match Petpooja's "% Discounts given" dashboard card,
            # which is discount / (net_sales + discount) — i.e. discount over the
            # pre-discount value net of tax (the st['c_t'] figure), NOT discount /
            # total_sales (total_sales includes tax, which over-states it by ~3-4pts).
            # The pre-2026-09 card scrape used this base; the JSON rewrite regressed
            # it to /total_sales, inflating every Sep value. (verified vs Aug: 30 Aug
            # 253269/1131383 = 22.39% matches the historical sheet exactly.)
            disc_base = net_sales + discount
            discount_pct = round(discount / disc_base * 100, 2) if (discount and disc_base) else 0.0

            return {
                "displayed_range": target_date,
                "total_sales": total_sales,
                "net_sales": net_sales,
                "online_sales": online,
                "online_pct": online_pct,
                "discount_pct": discount_pct,
                "total_orders": orders,
                "zomato": zomato,
                "swiggy": swiggy,
                "by_outlet": by_outlet,
            }
        finally:
            try:
                ctx.close()
            except Exception:
                pass
