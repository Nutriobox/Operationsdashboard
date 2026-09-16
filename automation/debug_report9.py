"""One-off: dump the exact outlet labels + Total Sales cells report 9 returns,
so we can fix the outlet aliases in weekly_sales_sync. Writes nothing."""
import re, sys
from datetime import date, timedelta
from bs4 import BeautifulSoup
import config
from browser_export import browser_custom_report

mon = date(2026, 8, 24); sun = mon + timedelta(days=6)
frm = f"{mon.isoformat()} 00:00:00"; to = f"{sun.isoformat()} 23:59:59"
anchor = 9960  # Prashant Vihar
html = browser_custom_report(config.REPORT_ALL_RESTAURANT_SALES, anchor, frm, to,
                             headless="--headed" not in sys.argv)
soup = BeautifulSoup(html, "html.parser")
for ti, table in enumerate(soup.find_all("table")):
    hs = [th.get_text(" ", strip=True) for th in table.find_all("th")]
    if not any(re.search(r"total\s*sales", h, re.I) and not re.search(r"net", h, re.I) for h in hs):
        continue
    ts_idx = next(i for i, h in enumerate(hs)
                  if re.search(r"total\s*sales", h, re.I) and not re.search(r"net", h, re.I))
    labels = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) <= ts_idx:
            continue
        label = tds[0].get_text(" ", strip=True)
        if label and label.lower() not in ("total", "min.", "max.", "avg.", "sub total"):
            labels.append(label)
        if re.search(r"noida|sector|63|advant|cloud", label, re.I):
            print(f"[table {ti}] NOIDA/SEC ROW:", repr(label),
                  "| TotalSales:", tds[ts_idx].get_text(strip=True))
    print(f"[table {ti}] OUTLET LABELS ({len(labels)}):", labels)

