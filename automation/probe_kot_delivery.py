"""Read-only probe: klist Delivery rows + pagination + Complete Duration format.
Output -> C:\\Users\\hp\\Downloads\\kot-probe-out.txt"""
from __future__ import annotations
import sys
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import config
from browser_export import PROFILE_DIR, _prime_kot_page, _is_logged_out
from playwright.sync_api import sync_playwright

BASE = config.PETPOOJA_BASE
DELIVERY = config.ORDER_TYPE_DELIVERY   # "1"
OID = 349767  # DLF
# a single completed business day window (Petpooja KOT format)
KOT_FROM, KOT_TO = "8 Sep 2026 01:00:00", "9 Sep 2026 01:00:00"
OUT = Path(r"C:\Users\hp\Downloads\kot-probe-out.txt")
lines=[]
def log(*a): s=" ".join(str(x) for x in a); print(s); lines.append(s)

# POST klist for DELIVERY only, optionally a page, return {records, rowcount, sampleRows, hasPager}
JS = r"""
async ([oid, start, end, delivery, page]) => {
  const b = new URLSearchParams();
  b.append('data[Kot][startdate]', start);
  b.append('data[Kot][enddate]', end);
  b.append('data[Kot][kot_id]',''); b.append('data[Kot][customer_name]','');
  b.append('data[Kot][customer_phone]',''); b.append('data[Kot][table_no]','');
  b.append('data[restaurant_id]', String(oid));
  b.append('data[current_page_url]', location.origin + '/items/kot_list/');
  b.append('data[Kot][order_type][]', delivery);
  if (page) b.append('page', String(page));
  let resp;
  try { resp = await fetch(location.origin + '/items/klist/?page=' + (page||1), {
    method:'POST', credentials:'include',
    headers:{'X-Requested-With':'XMLHttpRequest','Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'},
    body: b.toString() }); } catch(e){ return {err:'fetch '+e}; }
  const t = await resp.text();
  if (t.trim()==='9') return {sentinel:true};
  if (/UserLoginForm|\/users\/login/.test(t)) return {loggedOut:true};
  const rec = (t.match(/of\s+([0-9,]+)\s+records/i)||[])[1] || null;
  const doc = new DOMParser().parseFromString(t, 'text/html');
  const tables = [...doc.querySelectorAll('table')];
  let headers=[], rows=[];
  for (const tb of tables){
    const hs=[...tb.querySelectorAll('th')].map(x=>(x.textContent||'').trim()).filter(Boolean);
    if (hs.some(h=>/order\s*type/i.test(h)) || hs.some(h=>/complete\s*duration/i.test(h))){
      headers = hs;
      for (const tr of tb.querySelectorAll('tbody tr, tr')){
        const tds=[...tr.querySelectorAll('td')].map(x=>(x.textContent||'').replace(/\s+/g,' ').trim());
        if (tds.length>=headers.length-1 && tds.some(Boolean)) rows.push(tds);
      }
      break;
    }
  }
  // pager: look for pagination links / next
  const pager = /class="[^"]*paginat/i.test(t) || /page:\d+/.test(t) || />Next<|›|»/.test(t);
  return {records: rec, rowCount: rows.length, headers, sample: rows.slice(0,4), hasPager: pager, len: t.length};
}
"""

def main():
    with sync_playwright() as p:
        ctx=p.chromium.launch_persistent_context(user_data_dir=str(PROFILE_DIR),headless=True,args=["--disable-blink-features=AutomationControlled"])
        try:
            page=ctx.pages[0] if ctx.pages else ctx.new_page()
            _prime_kot_page(page,ctx,OID)
            if _is_logged_out(page): log("LOGGED OUT"); return
            ctx.request.post(BASE+"/", form={"header_changed_rest_id":str(OID)})
            page.wait_for_timeout(1200)
            for pg in (1,2):
                r=page.evaluate(JS,[OID,KOT_FROM,KOT_TO,DELIVERY,pg])
                log(f"=== page {pg}: records={r.get('records')} rowCount={r.get('rowCount')} hasPager={r.get('hasPager')} len={r.get('len')} ===")
                log(f"  headers: {r.get('headers')}")
                for row in (r.get('sample') or []):
                    log(f"  row: {row}")
        finally:
            ctx.close()
try: main()
finally:
    OUT.write_text("\n".join(lines),encoding="utf-8"); print("wrote",OUT)
