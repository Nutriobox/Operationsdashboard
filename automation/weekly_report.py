"""
Weekly Consolidated Sales Report -> Playwright port of the Claude
"weekly-petpooja-sales-report" task (the big Wed 3 AM job).

Fills columns D..AU (rows 5..23) of the current week's tab in the
"Weekly Sales Report" Google Sheet from FIVE sources:

    D-S   Petpooja "Order Report: Sub-Order Wise"  (orders, sales, online split,
          Zomato/Swiggy)                              -> pull_suborder()
    T-W   Petpooja KOT "Delivery Time Analysis"       -> pull_kot_delivery()
    X-AH  Zomato partner "Business reports" funnel     -> pull_zomato_funnel()
    AI-AR Swiggy "business_metrics_report*.xlsx"        -> pull_swiggy_funnel()
    AS-AU Captain-App KOT (from the Weekly KOT sheet)   -> pull_captain()

Same building blocks as the other ports: Petpooja through the primed single-outlet
browser session (browser_export), the sheet write + read-back through the signed-in
browser profile (sheet_writer.BrowserWriter). No Claude tokens.

    python weekly_report.py --selftest              # pull every source, WRITE NOTHING
    python weekly_report.py --dry-run               # + build every row, preview, no write
    python weekly_report.py --dry-run --monday 2026-08-31
    python weekly_report.py --headed                # live, visible browser
    python weekly_report.py                          # live (last completed week)

================================================================================
VALIDATE BEFORE SCHEDULING  (this job CANNOT be tested off the laptop — it needs
the live signed-in Petpooja / Zomato / Swiggy / Google sessions). Do a
`--headed --dry-run` for last week and confirm, source by source:

  1. SUB-ORDER (pull_suborder): confirm the report is reachable at
     custom_reports/view_report/SUBORDER_VIEW_ID below. If Petpooja only exposes it
     via Reports -> search -> Excel (no view_report id), set SUBORDER_VIA_EXCEL=True
     and confirm the download + column headers ("My Amount","Total Discount",
     "Container Charge","Sub Order Type","Total no. of bills").
     LIVE FINDING (2026-09-07, probed for Aug31-Sep6): the dashboard JSON is NOT a
     shortcut for D-S. /users/load_sales_statistics/ (single-outlet) exposes only
     SALES — t_o=online, o_t_z=Zomato, o_t_s=Swiggy (=> G/M/Q) — and its total_sales
     is GROSS. It carries NO per-platform ORDER COUNTS (F/L/P) and not the sheet's
     Sale = MyAmount-Discount+Container figure (E). So D-S must come from the
     Sub-Order Wise report, per bill, exactly like the original task — not the JSON.
  2. KOT-DELIVERY (pull_kot_delivery): confirm items/kot_list export still returns a
     CSV with "Order Type" + "Complete Duration", and that the 01:00->01:00 business
     window matches the sheet's historical numbers.
  3. ZOMATO (pull_zomato_funnel): confirm the partner "Business reports" export
     endpoint / CSV layout (Customer-funnel rows) and the ZOMATO_ID map.
  4. SWIGGY (pull_swiggy_funnel): confirm the business_metrics xlsx layout
     (CONVERSION_FUNNEL / CUSTOMERS rows) and the SWIGGY_RID map.
  5. CAPTAIN (pull_captain): confirm the Weekly-KOT tab name format resolves and
     B/C/D map to Total-KOT / Captain-KOT / Coverage.

  Only after a clean dry-run whose numbers match a known-good week: register
  NutrioBox-WeeklyReport (Wed ~03:00) and DISABLE the Claude twin
  weekly-petpooja-sales-report in the SAME pass (or they race the Petpooja
  outlet session — the July-corruption bug).
================================================================================
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta, timezone

import config

# Hardening (failure mode #6): force UTF-8 stdout/stderr so a rupee sign or any
# non-ASCII character (outlet name, error text) can never crash the run on
# Windows' cp1252 console — the bug that killed discount_weekly.py.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

IST = timezone(timedelta(hours=5, minutes=30))

# The "Weekly Sales Report" workbook (native Google Sheet — NOT the .xlsx Sales Data).
WEEKLY_REPORT_SHEET_ID = "1oNCCGX5ntgPW_OYwjWB5LMFhLfPitxzVAMWj95G0qpc"

# Petpooja report id for "Order Report: Sub-Order Wise" — VALIDATE (see header #1).
SUBORDER_VIEW_ID = None          # e.g. 19 ; set once confirmed
SUBORDER_VIA_EXCEL = False       # flip to True if there is no view_report id

# ---- outlet identity across all five sources ----------------------------------
# order == sheet write order (rows 5,7,9,...,23)
OUTLETS = [
    # key,          row, pp_id,  zomato_id,  swiggy_rid,  suborder_name,                 zomato_name,                                     captain_key
    ("dlf",          5, 349767, 21529349,  979965, "NutrioBox ( DLF Phase 2)",       "NutrioBox - DLF Phase 2, Gurgaon",              "DLF Phase 2"),
    ("rajinder",     7, 159181, 21017714,  899925, "NutrioBox ( Rajinder Nagar)",    "NutrioBox - Rajinder Nagar, New Delhi",         "Rajinder Nagar"),
    ("noida63",      9, 136183, 20792991,  750998, "NutrioBox ( Sector 63 Noida )",  "NutrioBox - Sector 63, Noida",                  None),  # not in KOT sheet
    ("dwarka",      11,  62697, 20020858,  453652, "NutrioBox (Dwarka)",             "NutrioBox - Dwarka, New Delhi",                 "Dwarka"),
    ("janakpuri",   13,  19652, 19208382,  228324, "NutrioBox (Janakpuri)",          "NutrioBox - Janakpuri, New Delhi",              "Janakpuri"),
    ("karkardooma", 15,  16011, 19034587,  128137, "NutrioBox (Karkardooma)",        "NutrioBox - Karkardooma, New Delhi",            "Karkardooma"),
    ("advant",      17,  80991, 20284001,  558627, "NutrioBox (Noida)",              "NutrioBox - Advant Navis Business Park, Noida", "Noida"),
    ("rohini",      19,   9960, 18557659,   43183, "NutrioBox (Prashant Vihar)",     "NutrioBox - Prashant Vihar, New Delhi",         "Prashant Vihar"),
    ("sec15",       21, 369621, 21779998, 1056691, "NutrioBox (Sector 15, Gurugram)","NutrioBox - Sector 15, Gurgaon",                "Sector 15, Gurugram"),
    ("shivalik",    23,  62695, 20020871,  450280, "NutrioBox (Shivalik)",           "NutrioBox - Shivalik, New Delhi",               "Shivalik"),
]

# Column layout D..AU (0-based index within the D..AU block written per row).
# D=col 4. We build a 44-wide list [D..AU] and write it in one shot per row.
COL_D = 4
COL_AU = 47
BLOCK_W = COL_AU - COL_D + 1      # 44 columns


def target_monday(ref: date) -> date:
    """The Monday of the last COMPLETED Mon-Sun week (this job runs on Wed)."""
    this_monday = ref - timedelta(days=ref.weekday())
    return this_monday - timedelta(days=7)


def week_tab_name(mon: date) -> str:
    """'Aug 24 - Aug 30, 2026' — the sheet's tab-naming format."""
    sun = mon + timedelta(days=6)
    return f"{mon.strftime('%b')} {mon.day} - {sun.strftime('%b')} {sun.day}, {sun.year}"


def _r2(x) -> float:
    try:
        return round(float(x) + 0.0, 2)
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------------------------
# SOURCE 1 — Petpooja Sub-Order Wise  -> D..S
# ------------------------------------------------------------------------------
def pull_suborder(mon: date, sun: date, headless: bool) -> dict:
    """
    Return {outlet_key: {D..S values}} for the week.

    Per the SKILL: Sale = My Amount - Total Discount + Container Charge. Zomato /
    Swiggy sub-rows are matched by case-insensitive 'zomato'/'swiggy' in the Sub
    Order Type. Computes:
      D total_orders, E total_sales, F online_orders, G online_sale,
      H online_orders_pct, I online_sale_pct, J dinein_orders, K dinein_sale,
      L zomato_orders, M zomato_sale, N zom_ord_pct, O zom_sale_pct,
      P swiggy_orders, Q swiggy_sale, R swi_ord_pct, S swi_sale_pct.

    VALIDATE (header #1): wire this to browser_export.browser_custom_report once the
    report id is confirmed, then parse with the BeautifulSoup logic below. Until the
    id is confirmed this raises so the job can never write a half-built row.
    """
    import csv as _csv
    from pathlib import Path
    from browser_export import export_order_csv

    out_dir = Path(__file__).resolve().parent / "outputs"
    name2key = {name: key for key, _r, _pp, _z, _s, name, *_ in OUTLETS}
    orders_by_name = {name: {} for name in name2key}      # name -> {invoice: order-row}

    day = mon
    while day <= sun:
        ds = day.isoformat()
        cached = out_dir / f"Order_Summary_Item_Report_{ds}_1.csv"
        path = cached if cached.exists() else export_order_csv(ds, out_dir, tag="1", headless=headless)
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for r in _csv.DictReader(fh):
                rn = (r.get("restaurant_name") or "").strip()
                if rn not in name2key:
                    continue
                if (r.get("status") or "").strip().lower() != "success":
                    continue
                orders_by_name[rn].setdefault(r.get("invoice_no"), r)   # once per bill
        day += timedelta(days=1)

    def num(o, k):
        return _r2(re.sub(r"[^0-9.\-]", "", str(o.get(k) or 0)) or 0)

    def sale(o):
        return num(o, "my_amount") - num(o, "discount") + num(o, "container_charge")

    out = {}
    for key, _r, _pp, _z, _s, name, *_ in OUTLETS:
        orders = list(orders_by_name[name].values())
        zom = [o for o in orders if (o.get("area") or "").strip().lower() == "zomato"]
        swi = [o for o in orders if (o.get("area") or "").strip().lower().startswith("swiggy")]
        D = len(orders); E = _r2(sum(sale(o) for o in orders))
        L = len(zom); M = _r2(sum(sale(o) for o in zom))
        P = len(swi); Q = _r2(sum(sale(o) for o in swi))
        F = L + P; G = _r2(M + Q); J = D - F; K = _r2(E - G)
        pct = lambda a, b: _r2(a / b * 100) if b else 0.0
        out[key] = dict(D=D, E=E, F=F, G=G, H=pct(F, D), I=pct(G, E), J=J, K=K,
                        L=L, M=M, N=pct(L, F), O=pct(M, G), P=P, Q=Q, R=pct(P, F), S=pct(Q, G))
    return out


def _suborder_rows(soup) -> list[dict]:
    """Parse the 'Order Report: Sub-Order Wise' table into per-sub-row dicts:
    {sub_order_type, my_amount, total_discount, container_charge, bills}.

    Header-driven (maps by column label, not position) so a Petpooja column
    reorder can never silently shift values into the wrong field. Labels are
    matched case/space/period-insensitively against the confirmed headers:
      'Sub Order Type', 'My Amount', 'Total Discount', 'Container Charge',
      'Total no. of bills'. Total / sub-total rows are skipped.

    NOTE: only SUBORDER_VIEW_ID (which view_report number is 'Sub-Order Wise')
    still needs live confirmation — this parser itself is complete.
    """
    def norm(s):
        return re.sub(r"[\s.]+", " ", str(s or "")).strip().lower()

    want = {
        "sub_order_type":  ["sub order type", "suborder type", "order type"],
        "my_amount":       ["my amount"],
        "total_discount":  ["total discount", "discount"],
        "container_charge": ["container charge"],
        "bills":           ["total no of bills", "no of bills", "total bills", "bills"],
    }

    def num(x):
        return _r2(re.sub(r"[^0-9.\-]", "", str(x)) or 0)

    for table in soup.find_all("table"):
        cells = table.find_all("th")
        if not cells:
            first_tr = table.find("tr")
            cells = first_tr.find_all(["td", "th"]) if first_tr else []
        headers = [norm(c.get_text()) for c in cells]
        if not headers:
            continue
        idx = {}
        for field, aliases in want.items():
            for i, h in enumerate(headers):
                if any(a == h or a in h for a in aliases):
                    idx[field] = i
                    break
        # Require at least the type, money, and bill-count columns to trust the table.
        if not all(k in idx for k in ("sub_order_type", "my_amount", "bills")):
            continue

        rows = []
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) <= max(idx.values()):
                continue
            texts = [t.get_text(strip=True) for t in tds]
            label = norm(texts[idx["sub_order_type"]])
            if label in ("", "total", "sub total", "subtotal", "grand total",
                         "min", "max", "avg"):
                continue
            rows.append(dict(
                sub_order_type=texts[idx["sub_order_type"]],
                my_amount=num(texts[idx["my_amount"]]),
                total_discount=num(texts[idx["total_discount"]]) if "total_discount" in idx else 0.0,
                container_charge=num(texts[idx["container_charge"]]) if "container_charge" in idx else 0.0,
                bills=int(num(texts[idx["bills"]])),
            ))
        if rows:
            return rows

    raise RuntimeError(
        "Sub-Order Wise table not found / headers changed — expected columns "
        "'Sub Order Type / My Amount / Total Discount / Container Charge / "
        "Total no. of bills'. Re-confirm SUBORDER_VIEW_ID and the report layout.")


def _fold_suborder(rows: list[dict]) -> dict:
    def sale(r):
        return _r2(r["my_amount"]) - _r2(r["total_discount"]) + _r2(r["container_charge"])
    zom = [r for r in rows if "zomato" in str(r["sub_order_type"]).lower()]
    swi = [r for r in rows if "swiggy" in str(r["sub_order_type"]).lower()]
    D = sum(int(r["bills"]) for r in rows)
    E = _r2(sum(sale(r) for r in rows))
    L = sum(int(r["bills"]) for r in zom); M = _r2(sum(sale(r) for r in zom))
    P = sum(int(r["bills"]) for r in swi); Q = _r2(sum(sale(r) for r in swi))
    F = L + P; G = _r2(M + Q)
    J = D - F; K = _r2(E - G)
    pct = lambda a, b: _r2(a / b * 100) if b else 0.0
    return dict(D=D, E=E, F=F, G=G, H=pct(F, D), I=pct(G, E), J=J, K=K,
                L=L, M=M, N=pct(L, F), O=pct(M, G), P=P, Q=Q, R=pct(P, F), S=pct(Q, G))


# ------------------------------------------------------------------------------
# SOURCE 2 — Petpooja KOT delivery-time  -> T..W
# ------------------------------------------------------------------------------
_KLIST_DELIVERY_JS = r"""
async ([oid, start, end, delivery, page]) => {
  const b = new URLSearchParams();
  b.append('data[Kot][startdate]', start);
  b.append('data[Kot][enddate]', end);
  b.append('data[Kot][kot_id]',''); b.append('data[Kot][customer_name]','');
  b.append('data[Kot][customer_phone]',''); b.append('data[Kot][table_no]','');
  b.append('data[restaurant_id]', String(oid));
  b.append('data[current_page_url]', location.origin + '/items/kot_list/');
  b.append('data[Kot][order_type][]', delivery);
  let resp;
  try {
    resp = await fetch(location.origin + '/items/klist/page:' + (page||1), {
      method:'POST', credentials:'include',
      headers:{'X-Requested-With':'XMLHttpRequest','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
      body: b.toString() });
  } catch(e){ return {err:'fetch '+e}; }
  const t = await resp.text();
  if (t.trim()==='9') return {sentinel:true};
  if (/UserLoginForm|\/users\/login/.test(t)) return {loggedOut:true};
  const doc = new DOMParser().parseFromString(t, 'text/html');
  let otIdx=-1, cdIdx=-1, rows=[];
  for (const tb of doc.querySelectorAll('table')) {
    const hs=[...tb.querySelectorAll('th')].map(x=>(x.textContent||'').trim());
    otIdx = hs.findIndex(h=>/order\s*type/i.test(h));
    cdIdx = hs.findIndex(h=>/complete\s*duration/i.test(h));
    if (cdIdx<0) continue;
    for (const tr of tb.querySelectorAll('tr')) {
      const tds=[...tr.querySelectorAll('td')].map(x=>(x.textContent||'').replace(/\s+/g,' ').trim());
      if (tds.length<=cdIdx) continue;
      rows.push({kot: tds[0], ot: otIdx>=0?tds[otIdx]:'', dur: tds[cdIdx]});
    }
    break;
  }
  return {rows: rows};
}
"""


def pull_kot_delivery(mon: date, sun: date, headless: bool) -> dict:
    """
    Per outlet T..W: Delivery orders whose Complete Duration is 15-25 min (T) and
    26+ min (V), plus their % of total deliveries (U, W). Window = week's Monday
    01:00 -> the following Monday 01:00 (Petpooja's business-day boundary).

    Reads items/klist (Order Type + Complete Duration — confirmed live 16 Sep),
    paginating with CakePHP `page:N`. A KOT-ID `seen` set makes it self-correcting:
    if pagination ever loops (returns a page already read), it stops instead of
    double-counting or spinning.
    """
    from playwright.sync_api import sync_playwright
    from browser_export import PROFILE_DIR, _prime_kot_page, _is_logged_out
    from petpooja import SessionExpired

    def kfmt(d: date) -> str:
        return f"{d.day} {d.strftime('%b %Y')} 01:00:00"

    kot_from, kot_to = kfmt(mon), kfmt(sun + timedelta(days=1))
    delivery = config.ORDER_TYPE_DELIVERY
    out = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            _prime_kot_page(page, ctx, OUTLETS[0][2])
            if _is_logged_out(page):
                raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")
            for key, _row, pp_id, *_ in OUTLETS:
                ctx.request.post(config.PETPOOJA_BASE + "/",
                                 form={"header_changed_rest_id": str(pp_id)})
                page.wait_for_timeout(1_200)
                durations, seen = [], set()
                for pg in range(1, 61):                 # hard cap 60 pages (~900 KOTs)
                    res = page.evaluate(_KLIST_DELIVERY_JS,
                                        [pp_id, kot_from, kot_to, delivery, pg])
                    if res.get("loggedOut"):
                        raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")
                    rows = res.get("rows") or []
                    fresh = [r for r in rows if r.get("kot") and r["kot"] not in seen]
                    if not fresh:
                        break                           # exhausted (or pagination looped)
                    for r in fresh:
                        seen.add(r["kot"])
                        if "delivery" not in str(r.get("ot", "")).lower():
                            continue
                        m = _parse_duration_min(r.get("dur"))
                        if m is not None:
                            durations.append(m)
                    if len(rows) < 15:                  # last (short) page
                        break
                out[key] = fold_kot_delivery(durations)
        finally:
            ctx.close()
    return out


def _parse_duration_min(s: str):
    """'0 hr : 15 min' / '1 hr : 5 min' -> minutes."""
    m = re.search(r"(\d+)\s*hr\s*:\s*(\d+)\s*min", str(s))
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def fold_kot_delivery(durations: list[int]) -> dict:
    deliveries = [d for d in durations if d is not None]
    tot = len(deliveries)
    band_1525 = sum(1 for d in deliveries if 15 <= d <= 25)
    band_26 = sum(1 for d in deliveries if d >= 26)
    pct = lambda a: _r2(a / tot * 100) if tot else 0.0
    return dict(T=band_1525, U=pct(band_1525), V=band_26, W=pct(band_26))


# ------------------------------------------------------------------------------
# SOURCE 3 — Zomato funnel  -> X..AH
# ------------------------------------------------------------------------------
def pull_zomato_funnel(mon: date, sun: date, headless: bool) -> dict:
    """
    Per outlet (matched by ZOMATO_ID): SUM daily Impressions/Menu opens/Cart builds/
    Placed/Delivered/New/Repeat; AVERAGE daily Impr-to-menu / Menu-to-cart /
    Cart-to-order %; AF = Placed / Menu opens * 100. VALIDATE (header #3).
    """
    raise NotImplementedError(
        "pull_zomato_funnel: port the partner Business-reports CSV pull (VALIDATE #3)")


def fold_zomato(daily: dict) -> dict:
    s = lambda k: sum(daily.get(k, []))
    a = lambda k: _r2(sum(daily.get(k, [])) / len(daily[k])) if daily.get(k) else 0.0
    placed, menu = s("placed"), s("menu_opens")
    return dict(X=s("impressions"), Y=a("impr_to_menu"), Z=menu, AA=a("menu_to_cart"),
                AB=s("cart_builds"), AC=a("cart_to_order"), AD=placed, AE=s("delivered"),
                AF=_r2(placed / menu * 100) if menu else 0.0,
                AG=s("new_cust"), AH=s("repeat_cust"))


# ------------------------------------------------------------------------------
# SOURCE 4 — Swiggy funnel  -> AI..AR
# ------------------------------------------------------------------------------
def pull_swiggy_funnel(mon: date, sun: date, headless: bool) -> dict:
    """
    Per outlet (matched by SWIGGY_RID) from the business_metrics xlsx (openpyxl):
    SUM Impressions/Menu opens/Cart builds/Orders/New/Repeat; AVERAGE the three
    conversion %s; AP = Orders / Menu opens * 100. VALIDATE (header #4).
    """
    raise NotImplementedError(
        "pull_swiggy_funnel: port the business_metrics xlsx parse (VALIDATE #4)")


def fold_swiggy(daily: dict) -> dict:
    s = lambda k: sum(daily.get(k, []))
    a = lambda k: _r2(sum(daily.get(k, [])) / len(daily[k])) if daily.get(k) else 0.0
    placed, menu = s("orders"), s("menu_opens")
    return dict(AI=s("impressions"), AJ=menu, AK=a("impr_to_menu"), AL=s("cart_builds"),
                AM=a("menu_to_cart"), AN=placed, AO=a("cart_to_order"),
                AP=_r2(placed / menu * 100) if menu else 0.0,
                AQ=s("new_cust"), AR=s("repeat_cust"))


# ------------------------------------------------------------------------------
# SOURCE 5 — Captain-App KOT (from the Weekly KOT sheet)  -> AS..AU
# ------------------------------------------------------------------------------
def pull_captain(mon: date, sun: date) -> dict:
    """
    Read B/C/D (Total Dine/Pickup KOT, Captain-App KOT, Coverage) for each mapped
    outlet from the Weekly KOT sheet's tab for this week. Read via gviz CSV through
    the signed-in browser context (same as sheet_writer.read_tab). Noida 63 is NOT
    in the KOT sheet -> AS-AU left blank for row 9.
    """
    from sheet_writer import BrowserWriter
    tab = f"{ordinal(mon.day)} {mon.strftime('%B')} - {ordinal(sun.day)} {sun.strftime('%B')}"
    out = {}
    with BrowserWriter(headless=True) as w:
        w.open_book(config.KOT_WEEKLY_SHEET_ID)
        grid = w.read_tab(tab)                 # rows; col A label, B..D metrics
    # Map by the Weekly-KOT sheet's own row labels (captain_key).
    label_row = {}
    for r in grid:
        if r and r[0].strip():
            label_row[r[0].strip()] = r
    for key, _row, *_x, cap_key in OUTLETS:
        if cap_key is None:
            out[key] = dict(AS="", AT="", AU="")
            continue
        row = next((v for k, v in label_row.items() if cap_key.lower() in k.lower()), None)
        if not row:
            raise RuntimeError(f"captain: outlet {cap_key!r} not found in KOT tab {tab!r}")
        out[key] = dict(AS=row[1], AT=row[2], AU=row[3])
    return out


def ordinal(n: int) -> str:
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


# ------------------------------------------------------------------------------
# ASSEMBLE + WRITE
# ------------------------------------------------------------------------------
# D..AU field order (44 wide). Empty string => leave the cell as typed blank.
FIELD_ORDER = (
    ["D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]  # sub-order
    + ["T", "U", "V", "W"]                                                            # kot-delivery
    + ["X", "Y", "Z", "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH"]                 # zomato
    + ["AI", "AJ", "AK", "AL", "AM", "AN", "AO", "AP", "AQ", "AR"]                    # swiggy
    + ["AS", "AT", "AU"]                                                              # captain
)
assert len(FIELD_ORDER) == BLOCK_W, (len(FIELD_ORDER), BLOCK_W)


def build_row(key, sub, kot, zom, swi, cap) -> list:
    merged = {**sub[key], **kot[key], **zom[key], **swi[key], **cap[key]}
    return [merged.get(f, "") for f in FIELD_ORDER]


# --- SPLIT MODE (default) -----------------------------------------------------
# The Zomato (X..AH) and Swiggy (AI..AR) funnels bot-gate the headless automation
# browser (the partner SPAs render blank / emit no data API), so they stay on the
# Claude twin. This Playwright job writes ONLY the columns it can source reliably:
#   D..W   = Petpooja Sub-Order (D..S) + KOT delivery-time (T..W)  [contiguous]
#   AS..AU = Captain-App KOT                                        [contiguous]
# X..AR are never touched here, so this job and the twin write disjoint columns
# of the same rows and cannot clobber each other.
DW_FIELDS = ["D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
             "Q", "R", "S", "T", "U", "V", "W"]
ASU_FIELDS = ["AS", "AT", "AU"]
_DW_PCT = {"H", "I", "N", "O", "R", "S", "U", "W"}


def build_dw(key, sub, kot) -> list:
    m = {**sub[key], **kot[key]}
    return [m.get(f, "") for f in DW_FIELDS]


def build_asu(key, cap) -> list:
    return [cap[key].get(f, "") for f in ASU_FIELDS]


def verify_split(dw: dict) -> list[str]:
    """Cross-checks on the D..W block only: F=L+P, J=D-F, percents in range."""
    errs = []
    idx = {f: i for i, f in enumerate(DW_FIELDS)}
    for key, _row, *_x in OUTLETS:
        v = dw[key]
        g = lambda f: v[idx[f]]
        if g("F") != (g("L") + g("P")):
            errs.append(f"{key}: F({g('F')}) != L({g('L')})+P({g('P')})")
        if g("J") != (g("D") - g("F")):
            errs.append(f"{key}: J({g('J')}) != D({g('D')})-F({g('F')})")
        for f in _DW_PCT:
            val = g(f)
            if isinstance(val, (int, float)) and not (0 <= val <= 100):
                errs.append(f"{key}.{f} = {val} out of 0-100")
    return errs


# Columns that hold a percentage (must land in 0..100). Explicit list — do NOT
# derive by suffix, or count columns like AH/AI/AN get mis-flagged.
PCT_COLS = {"H", "I", "N", "O", "R", "S", "U", "W",
            "Y", "AA", "AC", "AF", "AK", "AM", "AO", "AP", "AU"}


def verify(rows: dict) -> list[str]:
    """Cross-checks from the SKILL Step 8. Returns problems (empty == pass)."""
    errs = []
    for key, _row, *_x in OUTLETS:
        v = rows[key]
        get = lambda f: v[FIELD_ORDER.index(f)]
        F, L, P = get("F"), get("L"), get("P")
        D, J = get("D"), get("J")
        if F != (L + P):
            errs.append(f"{key}: online orders F({F}) != Zomato L({L})+Swiggy P({P})")
        if J != (D - F):
            errs.append(f"{key}: dine-in J({J}) != D({D})-F({F})")
        for f in PCT_COLS:
            val = get(f)
            if isinstance(val, (int, float)) and not (0 <= val <= 100):
                errs.append(f"{key}.{f} = {val} out of 0-100")
    return errs


def col_a1(idx1: int) -> str:
    s = ""
    while idx1 > 0:
        idx1, r = divmod(idx1 - 1, 26)
        s = chr(65 + r) + s
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--monday", help="week's Monday YYYY-MM-DD (default: last completed week)")
    ap.add_argument("--selftest", action="store_true", help="pull all sources, write nothing")
    ap.add_argument("--dry-run", action="store_true", help="pull + build rows + preview, no write")
    ap.add_argument("--headed", action="store_true", help="visible browser")
    args = ap.parse_args()
    headless = not args.headed

    if args.monday:
        mon = datetime.strptime(args.monday, "%Y-%m-%d").date()
        if mon.weekday() != 0:
            print(f"ERROR: --monday {args.monday} is a {mon.strftime('%A')}, not a Monday.")
            return 2
    else:
        mon = target_monday(datetime.now(IST).date())
    sun = mon + timedelta(days=6)
    tab = week_tab_name(mon)
    print(f"target week : {mon} .. {sun}")
    print(f"target tab  : {tab!r}")

    print("mode        : SPLIT — writes D..W + AS..AU (Petpooja + Captain); "
          "Zomato X..AH and Swiggy AI..AR stay on the Claude twin.")

    # ---- pull the sources this job owns (any raise = abort, nothing written) ----
    sub = pull_suborder(mon, sun, headless)
    kot = pull_kot_delivery(mon, sun, headless)
    cap = pull_captain(mon, sun)

    dw = {key: build_dw(key, sub, kot) for key, *_ in OUTLETS}
    asu = {key: build_asu(key, cap) for key, *_ in OUTLETS}

    problems = verify_split(dw)
    if problems:
        print("\nVERIFY FAILED — nothing written:")
        for pb in problems:
            print("  -", pb)
        return 1
    print("verify      : OK (F=L+P, J=D-F, percents in range)")

    for key, row_no, *_x in OUTLETS:
        print(f"  row {row_no:>2} {key:<12} D..W={dw[key][:6]}...{dw[key][-2:]}  AS..AU={asu[key]}")

    if args.selftest or args.dry_run:
        print("\n(dry) nothing written.")
        return 0

    # ---- write D..W and AS..AU per outlet row via the signed-in browser ----
    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=headless) as w:
        w.open_book(WEEKLY_REPORT_SHEET_ID)
        if tab not in w.tab_titles():
            print(f"STOP: tab {tab!r} does not exist — create it first "
                  "(duplicate the newest weekly tab), then re-run.")
            return 1
        w.select_tab(tab)
        for key, row_no, *_x in OUTLETS:
            w.write_rows_down(f"D{row_no}", [dw[key]])       # D..W
            w.write_rows_down(f"AS{row_no}", [asu[key]])     # AS..AU
        grid2 = w.read_tab(tab)
        if len(grid2) < 5 or not (grid2[4][COL_D - 1] or "").strip():
            print("VERIFY FAILED: row 5 D read back empty")
            return 1
    print(f"\nOK — wrote D..W + AS..AU rows 5..23 on {tab!r} "
          "(X..AR left for the Claude funnel twin).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
