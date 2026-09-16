"""
kot_list_probe.py  —  READ-ONLY diagnostic. Writes NOTHING to Petpooja/sheets.

Opens the AUTOMATION browser profile (the one kot_daily uses) and captures what it
actually renders for the dashboard and the KOT list, so we can see why priming
bounces. Saves screenshots + a JSON dump to automation/outputs/ (Claude can read
those directly from the mounted folder).

Run on the laptop:
    cd C:\\Users\\hp\\Downloads\\Operationsdashboard\\automation
    python kot_list_probe.py            # uses the persistent profile, headed
"""
from __future__ import annotations

import json
from pathlib import Path

import config

KOT_LIST_URL = f"{config.PETPOOJA_BASE}/items/kot_list/"
DASH_URL = f"{config.PETPOOJA_BASE}/users/dashboard"
PROFILE_DIR = config.SECRETS / "browser-profile"
OUT = config.ROOT / "outputs"
_LOGIN = ("UserLoginForm", "data[User][password]", "/users/login")

_DUMP = r"""
() => {
  const A = [...document.querySelectorAll('a[href]')];
  return {
    url: location.href,
    title: document.title,
    loggedOut: /UserLoginForm|\/users\/login/.test(document.documentElement.outerHTML),
    hasKotForm: !!document.getElementById('KotStartdate'),
    showing: (document.body.innerText.match(/Showing[^\n]*?records/i)||[null])[0],
    linkCount: A.length,
    kotLinks: A.filter(a=>/kot/i.test(a.href)||/kot/i.test(a.textContent||''))
               .map(a=>({href:a.getAttribute('href'), text:(a.textContent||'').trim().slice(0,30)})).slice(0,10),
    navTexts: [...new Set([...document.querySelectorAll('nav a, aside a, .sidebar a, ul li a')]
               .map(a=>(a.textContent||'').trim().replace(/\s+/g,' ').slice(0,28)).filter(Boolean))].slice(0,50),
    bodyLen: (document.body.innerText||'').length,
    bodyHead: (document.body.innerText||'').replace(/\s+/g,' ').slice(0,300),
  };
}
"""


def main():
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=False,
            args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            # 1) dashboard
            page.goto(DASH_URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            page.screenshot(path=str(OUT / "probe_1_dashboard.png"), full_page=True)
            report["dashboard"] = page.evaluate(_DUMP)

            # 2) direct goto kot_list (expected: bounce)
            page.goto(KOT_LIST_URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(5_000)
            page.screenshot(path=str(OUT / "probe_2_direct_kot.png"), full_page=True)
            report["direct_kot"] = page.evaluate(_DUMP)

            # 3) go back to dashboard, then SAME-ORIGIN script navigation to kot_list
            page.goto(DASH_URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(4_000)
            try:
                page.evaluate("u => { window.location.href = u; }", KOT_LIST_URL)
            except Exception as e:
                report["script_nav_err"] = str(e).splitlines()[0]
            page.wait_for_timeout(6_000)
            page.screenshot(path=str(OUT / "probe_3_scriptnav_kot.png"), full_page=True)
            report["script_nav_kot"] = page.evaluate(_DUMP)
        finally:
            ctx.close()

    (OUT / "probe_report.json").write_text(json.dumps(report, indent=2, default=str))
    print("\n=== PROBE DONE — wrote outputs/probe_report.json + 3 screenshots ===")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
