#!/usr/bin/env python3
"""
shrink_dashboard.py  (added 2026-10-21)

The Power-BI-style sales dashboard embeds TWO JSON arrays inline:
  * const DATA        = monthly aggregates            (~6 MB, fine)
  * const DAILY_DATA  = EVERY order line, with time   (~160 MB, the problem)

DAILY_DATA grew to ~729k rows / 163 MB (Sep 2025 -> now), pushing the whole
file to 172 MB. Two things broke:
  1. The Vercel proxy /api/sales-dashboard can't return >~4.5 MB gzip, so it
     served an empty body and the dashboard hung on "rendering".
  2. 172 MB is too much for a browser to parse/render.

SHRINK (approved by Satvik 2026-10-21):
  DAILY_DATA is kept ONLY for the last RECENT_DAYS (default 60). Older dates
  are dropped from DAILY_DATA and remain available at MONTHLY granularity via
  the untouched `DATA` array. The dashboard only consults DAILY_DATA when a
  specific date/range is selected, and the date picker is built from the dates
  present in DAILY_DATA — so this simply makes the picker offer the last
  RECENT_DAYS while the month view still covers all history.

  Why not keep daily detail for all dates: a year x 9 outlets x ~100 items is
  hundreds of thousands of rows (~6-8 MB gzip), which exceeds the Vercel proxy's
  ~4.5 MB response cap and is slow to render. 60 days of full order-line detail
  (incl. time-of-day) is ~4.2 MB gzip and renders ~4x lighter than the 172 MB
  original, while fitting the existing proxy with no app deploy.

  --older aggregate  keeps older dates at DAILY (no intraday) granularity
  instead of dropping them; larger file, only use with the Edge-proxy serving
  fix. Default is --older drop.

Every field the dashboard reads (restaurant, category, item, qty, date, time,
totalSales, status, isAddon) is preserved for retained rows, so charts are
unchanged. DATA and all the chart JavaScript are left byte-for-byte intact.

Usage:
  python shrink_dashboard.py <in.html> <out.html> [--days N] [--older drop|aggregate]
Exit 0 and prints before/after sizes. Non-zero on any problem (so a deploy
wrapper can fall back to the original file rather than upload a broken one).
"""
import sys
import json
import datetime
import argparse

RECENT_DAYS_DEFAULT = 60
MARKER = "const DAILY_DATA="


def find_array(html, marker):
    """Return (start_of_bracket, end_after_closing_bracket) for `marker[...]`."""
    i = html.find(marker)
    if i < 0:
        raise RuntimeError(f"marker {marker!r} not found")
    b = html.index("[", i)
    _, end = json.JSONDecoder().raw_decode(html, b)
    return b, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--days", type=int, default=RECENT_DAYS_DEFAULT)
    ap.add_argument("--older", choices=["drop", "aggregate"], default="drop")
    a = ap.parse_args()

    html = open(a.infile, "r", encoding="utf-8", errors="strict").read()
    before = len(html.encode("utf-8"))

    b, end = find_array(html, MARKER)
    rows = json.loads(html[b:end])
    n0 = len(rows)
    if n0 == 0:
        raise RuntimeError("DAILY_DATA is empty — refusing to rewrite")

    maxd = max(r["date"] for r in rows if r.get("date"))
    cutoff = (datetime.date.fromisoformat(maxd)
              - datetime.timedelta(days=a.days)).isoformat()

    recent = []
    agg = {}
    for r in rows:
        d = r.get("date", "")
        if d >= cutoff:
            recent.append(r)                     # full detail, untouched
            continue
        if a.older == "drop":
            continue                             # older -> monthly only (via DATA)
        key = (d, r.get("restaurant"), r.get("category"), r.get("item"),
               r.get("status"), r.get("isAddon"))
        cur = agg.get(key)
        if cur:
            cur["qty"] += r.get("qty", 0) or 0
            cur["totalSales"] += r.get("totalSales", 0) or 0
        else:
            nr = {"restaurant": r.get("restaurant"), "category": r.get("category"),
                  "item": r.get("item"), "qty": r.get("qty", 0) or 0,
                  "date": d, "time": "00:00",
                  "totalSales": r.get("totalSales", 0) or 0,
                  "status": r.get("status")}
            if r.get("isAddon") is not None:
                nr["isAddon"] = r.get("isAddon")
            agg[key] = nr

    new_rows = recent + list(agg.values())
    # keep the original compact style (same separators as the source)
    new_json = json.dumps(new_rows, separators=(", ", ": "), ensure_ascii=False)

    out = html[:b] + new_json + html[end:]
    # sanity: DATA and chart code must survive untouched
    for must in ["const DATA=", "new Chart", "Chart.register"]:
        if must not in out:
            raise RuntimeError(f"post-shrink sanity failed: {must!r} missing")
    open(a.outfile, "w", encoding="utf-8").write(out)
    after = len(out.encode("utf-8"))

    print(f"DAILY_DATA rows : {n0:,} -> {len(new_rows):,} "
          f"(recent {len(recent):,} full + {len(agg):,} aggregated)")
    print(f"cutoff (full>=) : {cutoff}   (last {a.days} days)")
    print(f"file size       : {before/1048576:.1f} MB -> {after/1048576:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
