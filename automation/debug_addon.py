"""Diagnostic: inspect Petpooja addon report (view_report/31) structure."""
import re
from pathlib import Path
import config
from petpooja import Petpooja

LOGS = config.LOGS
LOGS.mkdir(exist_ok=True)

pp = Petpooja.from_tokens()
oid = 349767
date = "2026-07-13"

print("switching outlet...")
pp.switch_outlet(oid)

# 1) raw GET of the report page
html = pp._get("/custom_reports/view_report/31")
(LOGS / "vr31_get.html").write_text(html, encoding="utf-8")
print(f"GET view_report/31: {len(html)} bytes")
print("  contains 're_filter_filed_':", "re_filter_filed_" in html)
print("  contains 're_pivot_table_1':", "re_pivot_table_1" in html)
ids = re.findall(r'id="([^"]*(?:filter|date|re_|pivot|restaurant)[^"]*)"', html, re.I)
print("  interesting ids (first 40):")
for i in ids[:40]:
    print("     ", i)
# look for any get_data_query group/report hints in inline JS
for m in re.findall(r"get_data_query/(\d+)/(\d+)", html)[:5]:
    print("  get_data_query hint:", m)

# 2) try a DIRECT POST using the field names from the SKILL (group 1 / report 23)
fields = {
    "re_filter_filed_1_23_0_from": date,
    "re_filter_filed_1_23_0_to": date,
    "re_filter_filed_1_23_3_dropdown": "",
    "selected_restaurant_id": str(oid),
    "selected_from_date": date,
    "selected_end_date": date,
}
try:
    r = pp._post("/custom_reports/get_data_query/1/23", fields,
                 headers={"X-Requested-With": "XMLHttpRequest"})
    body = r.text
    (LOGS / "vr31_post.html").write_text(body, encoding="utf-8")
    print(f"\nPOST get_data_query/1/23: {len(body)} bytes")
    print("  starts with '{':", body.lstrip()[:1] == "{")
    print("  contains 're_pivot_table_1':", "re_pivot_table_1" in body)
    print("  contains '<table':", "<table" in body.lower())
    print("  contains 'Total':", "Total" in body)
    print("  first 300 chars:", repr(body[:300]))
except Exception as e:
    print("POST failed:", e)

print("\nDEBUG_DONE_MARKER")
