"""Validate Source 1 (sub-order D-S) + Source 2 (kot-delivery T-W) for the last
completed week. WRITES NOTHING. Output -> C:\\Users\\hp\\Downloads\\weekly-test-out.txt"""
from __future__ import annotations
import sys
from datetime import date, timedelta
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import weekly_report as W

OUT = Path(r"C:\Users\hp\Downloads\weekly-test-out.txt")
lines=[]
def log(*a): s=" ".join(str(x) for x in a); print(s, flush=True); lines.append(s)

def main():
    mon = date(2026,9,7); sun = mon + timedelta(days=6)
    log(f"WEEK {mon}..{sun}")
    log("=== Source 1: sub-order D..S (from Order-Summary CSVs) ===")
    try:
        sub = W.pull_suborder(mon, sun, headless=True)
        for key,_r,_pp,_z,_s,name,*_ in W.OUTLETS:
            v=sub[key]
            ok = (v['F']==v['L']+v['P']) and (v['J']==v['D']-v['F'])
            log(f"  {key:<11} D(orders)={v['D']:<5} E(sale)={v['E']:<12} online F={v['F']} (Z L={v['L']} S P={v['P']}) dinein J={v['J']}  consistent={ok}")
        tot_orders = sum(sub[k]['D'] for k,*_ in W.OUTLETS)
        tot_sale   = round(sum(sub[k]['E'] for k,*_ in W.OUTLETS),2)
        log(f"  WEEK TOTAL: orders={tot_orders}  sale(E)={tot_sale}")
    except Exception as e:
        log(f"  SOURCE1 ERROR: {type(e).__name__}: {str(e).splitlines()[0]}")
    log("=== Source 2: kot-delivery T..W (paginated klist) ===")
    try:
        kot = W.pull_kot_delivery(mon, sun, headless=True)
        for key,_r,_pp,_z,_s,name,*_ in W.OUTLETS:
            v=kot[key]; total_deliv = v['T']+v['V']
            log(f"  {key:<11} deliveries={total_deliv:<5} 15-25min T={v['T']} ({v['U']}%)  26+min V={v['V']} ({v['W']}%)")
    except Exception as e:
        log(f"  SOURCE2 ERROR: {type(e).__name__}: {str(e).splitlines()[0]}")

try: main()
finally:
    OUT.write_text("\n".join(lines), encoding="utf-8"); print("wrote", OUT)
