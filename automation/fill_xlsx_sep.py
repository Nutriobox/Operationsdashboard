"""
One-off: fill/correct September 2026 in the OLD .xlsx "Sales Data" (1r9u4...) so it
matches the native sheet. The .xlsx can't take the Sheets API, so this uses the
browser (UI) writer — the flaky one — but writes each day's WHOLE row in a single
Name-Box hop (robust) and retries, rather than dozens of single-cell edits.

Values come from Petpooja over HTTP (same source as the native), so discount is the
correct card-basis value and every column is filled.

  python fill_xlsx_sep.py --dry-run     locate rows + preview, write nothing
  python fill_xlsx_sep.py               live: rewrite each Sep row, read back P

Safe-ish: writes only the September 2026 day rows (found by column-A label, verified
on the live sheet before writing). Re-runnable.
"""
from __future__ import annotations
import argparse, json, ssl, urllib.parse, urllib.request, sys, time
from datetime import date, datetime, timedelta
import config
from daily_sheet import WEEKDAY_TAB, COLUMN_OUTLET, build_row, row_label, _norm_daylabel
from dashboard_scrape import _RES_NAME
from sheet_writer import BrowserWriter

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

XLSX_ID = "1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs"   # the OLD .xlsx (main sheet Satvik edits)
BASE = "https://billing.petpooja.com"

def num(s):
    try: return float(str(s).replace(",","").strip())
    except: return 0.0

def post(ep, d, cookie):
    body=urllib.parse.urlencode({"from_date":d,"to_date":d}).encode()
    rq=urllib.request.Request(BASE+ep,data=body,headers={"Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest","Cookie":cookie,"User-Agent":"Mozilla/5.0"})
    c=ssl.create_default_context();c.check_hostname=False;c.verify_mode=ssl.CERT_NONE
    return json.loads(urllib.request.urlopen(rq,timeout=45,context=c).read().decode())

def pull(d, cookie):
    rw=post("/users/load_restaurants_wise_data/",d,cookie)
    st=post("/users/load_sales_statistics/",d,cookie).get("Statistics_data") or {}
    by={}
    for e in rw.get("all_restaurant_statistics",[]):
        rid=e.get("res_id")
        if rid in (0,None): continue
        nm=_RES_NAME.get(int(rid))
        if nm: by[nm]={"total":num(e.get("total_sales"))}
    ts=num(st.get("total_sales")); net=num(st.get("t_net")); online=num(st.get("t_o")); disc=num(st.get("total_discount"))
    return {"by_outlet":by,"total_sales":ts,"net_sales":net,"online_sales":online,
            "zomato":num(st.get("o_t_z")),"swiggy":num(st.get("o_t_s")),
            "total_orders":int(num(st.get("total_orders"))),
            "online_pct":round(online/ts*100,2) if ts else 0.0,
            "discount_pct":round(disc/(net+disc)*100,2) if (net+disc) else 0.0}

def find_row(grid, label):
    want=_norm_daylabel(label)
    for i,r in enumerate(grid,start=1):
        if r and want is not None and _norm_daylabel(r[0])==want: return i
    return None

def retry(fn, tries=4, wait=1.5):
    last=None
    for k in range(tries):
        try: return fn()
        except Exception as e:
            last=e; time.sleep(wait*(k+1))
    raise last

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--dry-run",action="store_true")
    a=ap.parse_args()
    if a.date: dates=[datetime.strptime(a.date,"%Y-%m-%d").date()]
    else:
        d0=date(2026,9,1); dates=[d0+timedelta(days=i) for i in range((date(2026,9,27)-d0).days+1)]
    cookie=json.load(open(config.SECRETS/"tokens.json"))["petpooja_cookie"]
    payload={}
    for d in dates:
        data=pull(d.isoformat(),cookie)
        ssum=sum(data["by_outlet"].get(n,{}).get("total",0) for _,n in COLUMN_OUTLET)
        if abs(ssum-data["total_sales"])>2 or not data["net_sales"]:
            print(f"SKIP {d} sanity (sum={ssum:.0f} tot={data['total_sales']:.0f})"); continue
        payload[d]=data
    ok=[]; fail=[]
    with BrowserWriter(headless=True) as w:
        w.open_book(XLSX_ID)
        grids={}
        for d in dates:
            if d not in payload: continue
            tab=WEEKDAY_TAB[d.weekday()]; label=row_label(d)
            try:
                w.select_tab(tab)
                if tab not in grids: grids[tab]=retry(lambda: w.read_tab(tab))
                row=find_row(grids[tab],label)
                if row is None:
                    print(f"!! {label} ({tab}): no row label — SKIP"); fail.append(label); continue
                want=_norm_daylabel(label)
                if _norm_daylabel(retry(lambda: w.read_selected_value(f"A{row}")))!=want:
                    corr=None
                    for cand in (row+1,row-1):
                        if cand>=1 and _norm_daylabel(retry(lambda: w.read_selected_value(f"A{cand}")))==want:
                            corr=cand; break
                    if corr is None:
                        print(f"!! {label} ({tab}) row {row}: label mismatch — SKIP"); fail.append(label); continue
                    row=corr
                values=build_row(payload[d],row)
                if a.dry_run:
                    print(f"  ~ {label} ({tab}) B{row}:U{row}  P={values[14]}  (dry-run)"); ok.append(label); continue
                retry(lambda: (w.select_tab(tab), w.write_rows_down(f"B{row}",[values])))
                back=retry(lambda: w.read_selected_value(f"P{row}"))
                good = back.replace(" ","").rstrip("%")==f"{payload[d]['discount_pct']:.2f}"
                print(f"  {'OK' if good else 'CHECK'} {label} ({tab}) row{row}: P read-back {back!r}")
                (ok if good else fail).append(label)
            except Exception as e:
                print(f"  FAIL {label} ({tab}): {str(e).splitlines()[0][:90]}"); fail.append(label)
    print(f"\ndone: ok={len(ok)} fail={len(fail)}  {('FAILED: '+str(fail)) if fail else ''}")
    return 1 if fail else 0

if __name__=="__main__":
    raise SystemExit(main())
