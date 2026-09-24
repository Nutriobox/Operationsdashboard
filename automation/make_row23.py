# Read-only helper: scrape 23 Sep sales and emit a paste-ready row for Wed!B67:U67.
# Writes nothing to any sheet. Reuses the exact scrape + build_row the daily job uses.
import daily_sheet as ds

DATE = "2026-09-23"
ROW  = 67
target = ds.resolve_target(DATE)
label  = ds.row_label(target)
tab    = ds.WEEKDAY_TAB[target.weekday()]

data = ds.scrape_daily(target.isoformat(), headless=True)
errs = ds.sanity(data)
vals = ds.build_row(data, ROW)              # B..U (20 values); index 11 = M = ""
cols = list("BCDEFGHIJKLMNOPQRSTU")

lines = []
lines.append(f"date={DATE}  tab={tab}  label={label}  row={ROW}")
lines.append(f"sanity={'OK' if not errs else errs}")
lines.append(f"total_sales={data['total_sales']:,.0f}  net={data['net_sales']:,.0f}  orders={data['total_orders']}")
lines.append("PER_CELL:")
for c, v in zip(cols, vals):
    lines.append(f"  {c}{ROW} = {v}")
lines.append("PASTE_TSV (click B67, then Ctrl+V):")
lines.append("\t".join(str(v) for v in vals))
text = "\n".join(lines)
print(text)
with open("logs/_row23.txt", "w", encoding="utf-8") as f:
    f.write(text + "\n")
print("\n[written to logs\\_row23.txt]")
