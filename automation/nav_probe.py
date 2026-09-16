"""Read-only diagnostic: why won't the Name Box navigate on the Sales Data .xlsx?
Writes NOTHING. Run headed:  python nav_probe.py
Copy ALL the output back to Claude."""
import time, config
from playwright.sync_api import sync_playwright

SID = "1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs"
PROFILE = str(config.SECRETS / "browser-profile")
URL = f"https://docs.google.com/spreadsheets/d/{SID}/edit"

def nb(pg):
    return pg.evaluate("()=>{var b=document.querySelector('#t-name-box');"
                       "return b?(b.value||b.textContent||''):'<<no #t-name-box>>';}")

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        PROFILE, headless=False, viewport={"width":1600,"height":1000},
        args=["--disable-blink-features=AutomationControlled","--window-size=1600,1000"])
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.set_default_timeout(45000)
    pg.goto(URL, wait_until="domcontentloaded")
    time.sleep(5)
    print("URL        :", pg.url)
    print("signed-in? :", "accounts.google.com" not in pg.url)

    dump = pg.evaluate("""()=>{
      var b=document.querySelector('#t-name-box');
      var vo=document.querySelector('.docs-titlebar-badges, .docs-view-only, [aria-label*=\"View only\"]');
      var editable = !!document.querySelector('#t-formula-bar-input');
      var inputs=[...document.querySelectorAll('input,div')].filter(function(e){
          return /name-box|waffle-name/.test(e.className||'');})
          .slice(0,6).map(function(e){return {tag:e.tagName,id:e.id,cls:(e.className||'').slice(0,40),
          val:(e.value||e.textContent||'').slice(0,20)};});
      return {nb: b?{tag:b.tagName,id:b.id,cls:b.className,val:b.value,txt:(b.textContent||'').slice(0,20),
              vis:!!(b.offsetWidth||b.offsetHeight)}:null,
              viewOnlyBadge: vo?vo.textContent.trim().slice(0,40):null,
              hasFormulaBar: editable, nameBoxCandidates: inputs};
    }""")
    import json; print("DOM        :", json.dumps(dump, indent=2)[:1500])

    print("\n-- start name box =", repr(nb(pg)))
    box = pg.locator("#t-name-box")

    box.click(); box.press("Control+A"); box.press("Delete"); box.type("A65", delay=40); box.press("Enter")
    time.sleep(1.4); print("S1 type+Enter        ->", repr(nb(pg)))

    box.click(); box.fill("A65"); box.press("Enter")
    time.sleep(1.4); print("S2 fill+Enter        ->", repr(nb(pg)))

    box.click(); box.fill("A65"); pg.keyboard.press("Enter"); pg.keyboard.press("NumpadEnter")
    time.sleep(1.4); print("S3 fill+Enter+Numpad ->", repr(nb(pg)))

    # is a suggestion/autocomplete dropdown intercepting Enter?
    drop = pg.evaluate("()=>{var d=document.querySelector('.docs-gm-autocomplete, .waffle-nameinput-autocomplete, [role=listbox]');return d?d.textContent.slice(0,60):null;}")
    print("autocomplete dropdown:", repr(drop))
    print("\nLeaving browser open 25s — look at it, note any dialog/banner/'Viewing' label.")
    time.sleep(25)
    ctx.close()
