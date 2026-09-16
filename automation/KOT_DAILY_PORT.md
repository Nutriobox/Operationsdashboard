# Daily KOT Comparison → Playwright + HTTP (port of `daily-kot-comparison`)

Moves the daily KOT task off Claude. The pull is deterministic; the sheet writes
go through the signed-in Google Sheets UI with Playwright (not Claude, and not
the Sheets API — see "Why the browser writes" below).

## What runs

```
petpooja.py       kot_count()      Total Dine In/Pickup KOT — plain HTTP POST /items/klist/
browser_export.py scrape_captain_kots()  Captain App KOT — Playwright (view_report/27 is JS-rendered)
sheet_writer.py   BrowserWriter    writes both sheets through the Google Sheets web UI as mayank@
kot_daily.py      orchestrator     --selftest / --dry-run / --headed / live
```

Pipeline = pull all 9 outlets (KOT via HTTP, Captain via one browser session) →
sanity gates (Captain ≤ Total, no zero outlets) → ensure/duplicate the SOURCE
day tab and write B2:C10 → find the next empty block in the DESTINATION and write
B:L → every write is read back through gviz and compared before it's trusted.

## What broke and was fixed (2026-08-24)

Petpooja changed two pages; the ported client (written 3 Aug, never run) was
stale, so both readers were repaired and re-verified:

- **KOT list moved.** Posting filters to `/items/kot_list/` now returns the page
  shell with no "Showing 1..N" line. The results fragment is a separate endpoint,
  `POST /items/klist/`, which needs the full field set (`data[restaurant_id]`,
  `data[current_page_url]`) plus the `X-Requested-With`/`Referer` headers, and it
  returns the sentinel `"9"` ("reload the parent page") until the `kot_list` shell
  has been primed and the outlet switch has committed. `kot_count` now primes the
  shell, and on the sentinel it re-switches the outlet and retries with back-off
  (the "outlet-session collision" the old skills warned about).
- **Captain Performance Report is JS-rendered.** `view_report/27` no longer ships
  the `re_filter_filed_*` inputs in the HTML, and its data endpoint
  (`get_data_query/1/19`) returns 403 to a direct POST. It's now scraped in the
  browser (`scrape_captain_kots`), reading the pivot's Total-row "No of Kots"
  cell, with the same outlet-switch verify-and-retry.

Verified against ground truth: the pull for business day 23 Aug 2026 matches, cell
for cell, the numbers the Claude task collected that morning (it collected fine
but was blocked writing — see below). Totals 643 KOT / 597 Captain.

## Why the browser writes (and why it will work where Claude didn't)

The DESTINATION workbook "Sales Data" is an uploaded **Excel (.xlsx)** file in
Drive. The Google Sheets API rejects those ("must not be an Office file"), so the
API port could never have worked for the destination. Both sheets are therefore
written through the Sheets **web UI**, as the signed-in user.

The Claude run on 23 Aug failed at exactly this step — tab duplication — because
of Claude-in-Chrome specifics: CDP `captureScreenshot` froze while the tab menu
was open, the viewport kept resizing between tool calls so click coordinates went
stale, and synthetic DOM events were rejected as untrusted. Headless Playwright
has none of these: a **fixed 1600×1000 viewport**, **no screenshot dependency**,
and **real trusted** mouse/keyboard events. Writes are canvas-free — the Name Box
(`#t-name-box`) moves the selection and the keyboard (Tab/Enter) enters values —
and every write is read back through gviz.

## Validate on the laptop before cutover (needs the signed-in Google profile)

The pull is fully verifiable headless; the **writes can only be exercised where
the browser profile is signed in to Google** (this laptop). Do this before
scheduling:

1. Session checks:
   ```
   python refresh_tokens.py --check          REM Petpooja must be ok
   python kot_daily.py --selftest            REM both readers healthy
   ```
   If `--selftest` reports the Google session isn't signed in, run `DELAY-LOGIN.bat`
   once (sign in as mayank@nutriobox.com, close the window).
2. **Watch it write, headed**, for a day that's genuinely missing (23 Aug never
   got written):
   ```
   python kot_daily.py --headed --date 2026-08-23
   ```
   Confirm: a "23rd August" tab is created at the left of the SOURCE sheet with
   B2:C10 filled, and a new "23rd August" block appears in the DESTINATION
   "Daily KOT Comparsion" tab. The run self-verifies via gviz and aborts on any
   mismatch, so a clean exit means the numbers landed.
3. From then on, the normal run (yesterday, headless) is just:
   ```
   python kot_daily.py
   ```

## Go live

Only after step 2 passes:

1. Disable the Claude task so the two don't both write:
   (Cowork) disable scheduled task **daily-kot-comparison**.
2. Register the Windows job:
   ```
   KOT-DAILY-SCHEDULE.bat        REM creates NutrioBox-KOT-Daily, daily 05:15 IST
   ```

`kot_daily.py` is idempotent: if the day's tab/block already holds data it refuses
to overwrite, so an accidental double-run is safe.

## Not yet ported

Weekly (`kot-comparsion`) and monthly (`monthly-kot-comparison`) still run on
Claude. They reuse the same `petpooja.py` + `browser_export.py` + `sheet_writer.py`
building blocks; only the date windows, sheet ids, and tab-naming differ.
