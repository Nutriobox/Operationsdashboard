"""Zomato discovery v3: on the WORKING offers page, capture its API calls,
dump all links, screenshot. Output txt + png to Downloads."""
from __future__ import annotations
import sys
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
from browser_export import PROFILE_DIR
from playwright.sync_api import sync_playwright

RESID = 21529349
OFFERS = f"https://www.zomato.com/partners/onlineordering/offers/trackOffers?resId={RESID}"
OUT = Path(r"C:\Users\hp\Downloads\zomato-probe-out.txt")
PNG = Path(r"C:\Users\hp\Downloads\zomato-offers.png")
lines=[]; reqs=[]
def log(*a): lines.append(" ".join(str(x) for x in a))

def main():
    with sync_playwright() as p:
        ctx=p.chromium.launch_persistent_context(user_data_dir=str(PROFILE_DIR),headless=True,
            viewport={"width":1400,"height":1000}, args=["--disable-blink-features=AutomationControlled"])
        try:
            page=ctx.pages[0] if ctx.pages else ctx.new_page()
            page.on("request", lambda r: reqs.append((r.method, r.url)) if r.resource_type in ("xhr","fetch") else None)
            try: page.goto(OFFERS, wait_until="networkidle", timeout=60000)
            except Exception as e: log("nav:",str(e).splitlines()[0])
            page.wait_for_timeout(5000)
            log(f"final url={page.url}")
            log("=== API endpoints the OFFERS page calls (host+path) ===")
            seen=set()
            for m,u in reqs:
                base=u.split('?')[0]
                if base in seen: continue
                seen.add(base)
                if any(k in u for k in ("zomato.com","zoma.to")) and not any(x in u for x in (".js",".css",".png",".svg",".woff",".jpg",".gif")):
                    log(f"  {m} {base}")
            log(f"(total distinct api-ish: {len(seen)})")
            log("=== ALL nav links (partner routes) ===")
            hrefs = page.evaluate("""()=>{
              const s=new Set();
              document.querySelectorAll('a[href]').forEach(a=>{const h=a.getAttribute('href')||'';
                if(h.includes('/partners/')) s.add((a.textContent||'').replace(/\\s+/g,' ').trim().slice(0,30)+' :: '+h.split('?')[0]);});
              return [...s].slice(0,60);
            }""")
            for h in hrefs: log("  "+h)
            try:
                page.screenshot(path=str(PNG), full_page=False)
                log("screenshot saved")
            except Exception as e:
                log("screenshot err:", str(e).splitlines()[0])
        finally:
            ctx.close()
try: main()
finally: OUT.write_text("\n".join(lines),encoding="utf-8"); print("wrote",OUT)
