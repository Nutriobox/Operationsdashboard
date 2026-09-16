"""Read-only probe: discover the Petpooja 'Sub-Order Wise' custom-report id and
dump layouts for the Weekly Report port. Writes NOTHING to any sheet/report.
Output -> C:\\Users\\hp\\Downloads\\weekly-probe-out.txt"""
from __future__ import annotations
import sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import config
from browser_export import PROFILE_DIR, _prime_kot_page, _is_logged_out
from playwright.sync_api import sync_playwright

BASE = config.PETPOOJA_BASE
PRIME_OID = 349767            # DLF Phase 2
FROM_DT, TO_DT = "2026-09-07 00:00:00", "2026-09-13 23:59:59"
OUT = Path(r"C:\Users\hp\Downloads\weekly-probe-out.txt")
lines = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s); lines.append(s)

SET_DATES = """([f,t])=>{let n=0;document.querySelectorAll('input[id^="re_filter_filed_"]').forEach(el=>{if(/_from$/.test(el.id)){el.removeAttribute('readonly');el.value=f;el.dispatchEvent(new Event('change',{bubbles:true}));n++;}if(/_to$/.test(el.id)){el.removeAttribute('readonly');el.value=t;el.dispatchEvent(new Event('change',{bubbles:true}));n++;}});return n;}"""

def dump_first_table_headers(page, tag):
    js = """()=>{for(const tb of document.querySelectorAll('table')){const ths=[...tb.querySelectorAll('th')].map(t=>(t.textContent||'').trim()).filter(Boolean);let hdr=ths;if(!hdr.length){const tr=tb.querySelector('tr');hdr=tr?[...tr.querySelectorAll('td,th')].map(c=>(c.textContent||'').trim()):[];}if(hdr.length>=3)return hdr;}return [];}"""
    try:
        hdr = page.evaluate(js)
        log(f"  [{tag}] header cells ({len(hdr)}): {hdr}")
    except Exception as e:
        log(f"  [{tag}] header dump error: {str(e).splitlines()[0]}")

def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(user_data_dir=str(PROFILE_DIR), headless=True,
              args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            _prime_kot_page(page, ctx, PRIME_OID)
            if _is_logged_out(page):
                log("PETPOOJA LOGGED OUT — run refresh_tokens.py --login"); return
            log("=== 1) enumerate custom reports (find Sub-Order Wise) ===")
            found = {}
            for path in ["/custom_reports", "/custom_reports/index", "/reports", "/users/dashboard"]:
                try:
                    page.goto(BASE + path, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(1500)
                except Exception as e:
                    log(f"  [nav {path}] {str(e).splitlines()[0]}"); continue
                anchors = page.eval_on_selector_all(
                    "a[href*='view_report/']",
                    "els=>els.map(e=>({href:e.getAttribute('href'),text:(e.textContent||'').replace(/\\s+/g,' ').trim()}))")
                log(f"  --- {path}: {len(anchors)} view_report links ---")
                for a in anchors:
                    import re
                    m = re.search(r"view_report/(\d+)", a["href"] or "")
                    if not m: continue
                    rid = m.group(1); found[rid] = a["text"] or found.get(rid, "")
                    log(f"    view_report/{rid}   |   {a['text']}")
            log(f"  === report id -> name map: {found}")
            subid = next((rid for rid, nm in found.items() if "sub" in nm.lower() and "order" in nm.lower()), None)
            log(f"  >>> Sub-Order Wise candidate id: {subid}")

            log("=== 2) dump Sub-Order report headers (DLF, 7-13 Sep) ===")
            if subid:
                try:
                    page.goto(f"{BASE}/custom_reports/view_report/{subid}", wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_selector('[id^="re_filter_filed_"]', timeout=20000)
                    page.evaluate(SET_DATES, [FROM_DT, TO_DT])
                    for sel in ("input.re_final_search","button.re_final_search","#re_search",'button:has-text("Search")'):
                        loc = page.locator(sel)
                        if loc.count(): loc.first.click(timeout=8000); break
                    page.wait_for_timeout(6000)
                    dump_first_table_headers(page, "suborder")
                except Exception as e:
                    log(f"  suborder dump error: {str(e).splitlines()[0]}")
            else:
                log("  (skipped — id not found; check the report-name map above)")

            log("=== 3) dump KOT list columns (source 2 planning) ===")
            try:
                page.goto(f"{BASE}/items/kot_list/", wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2500)
                dump_first_table_headers(page, "kot_list")
            except Exception as e:
                log(f"  kot_list error: {str(e).splitlines()[0]}")
        finally:
            ctx.close()

try:
    main()
finally:
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT)
