# Monthly KOT Comparison → Playwright + HTTP (port of `monthly-kot-comparison`)

Moves the monthly KOT task off Claude, reusing the same building blocks as the
daily/weekly ports (`petpooja.py` + `browser_export.py` + `sheet_writer.py`,
shared pull/write in `kot_common.py`). Only the date window, sheet id, and tab
naming differ.

## What runs

```
petpooja.py       kot_count()            Total Dine In/Pick Up KOT — HTTP POST /items/klist/
browser_export.py scrape_captain_kots()  Captain App KOT — Playwright (view_report/27 is JS-rendered)
kot_common.py     pull/sanity/write_source  shared with kot_weekly.py
kot_monthly.py    orchestrator           --selftest / --dry-run / --headed / live
```

Pipeline = pull all 9 outlets for the month → sanity gates (Captain ≤ Total, no
zero outlets) → create/find the month tab and write **B2:C10 only** → read every
write back through gviz and compare.

## Window & naming (matches the SKILL exactly)

- Target = the calendar month that just **ended** (the month of yesterday).
- Both filters span **[1st of that month 00:00:00 → 1st of next month 00:00:00)**.
  KOT format `1 Jul 2026 00:00:00`; Captain format `2026-07-01 00:00:00`.
- Tab name = the month's full name + year, e.g. `July 2026`.

## Differences from the daily port

- **Source-only.** No "Sales Data" mirror — writes just the Monthly KOT sheet
  (`config.KOT_MONTHLY_SHEET_ID`).
- **A1 is never written** (it's the `Outlets` header). `write_source(..., write_a1=False)`.
- **Idempotency built in.** If a tab named exactly `"<Month> <Year>"` already
  exists (the `July 2026` template, or a re-run), it is selected and filled in
  place — no duplicate is created. Otherwise the newest (leftmost) tab is
  duplicated and moved to position 0. This matches the SKILL's "idempotency check
  first" step.

## Validate on the laptop before cutover (needs the signed-in Google profile)

1. Session + reader liveness:
   ```
   python refresh_tokens.py --check          REM Petpooja must be ok
   python kot_monthly.py --selftest          REM both readers healthy
   ```
   If `--selftest` says the Google session isn't signed in, run `DELAY-LOGIN.bat`
   once (sign in as mayank@nutriobox.com, close the window).
2. Dry-run the target month and eyeball the 18 numbers:
   ```
   python kot_monthly.py --dry-run
   ```
3. **Watch it write, headed**, for a month you can verify (e.g. fill the
   `July 2026` template, or backfill a specific month):
   ```
   python kot_monthly.py --headed --month 2026-07
   ```
   Confirm a `July 2026` tab holds B2:C10; D (coverage) and row 11 (TOTAL) recalc.
   The run self-verifies via gviz and aborts on any mismatch.
4. From then on the normal run (previous calendar month, headless) is just:
   ```
   python kot_monthly.py
   ```

## Go live

Only after step 3 passes:

1. Disable the Claude task so the two don't both write:
   (Cowork) disable scheduled task **monthly-kot-comparison**.
2. Register the Windows job:
   ```
   KOT-MONTHLY-SCHEDULE.bat       REM creates NutrioBox-KOT-Monthly, 1st @ 12:30 IST
   ```

Adjust the day-1 time in `KOT-MONTHLY-SCHEDULE.bat` if it ever clashes with the
`nutriobox-monthly-dashboard` (~11:15) or `petpooja-sales-to-gsheet` (~10:30) runs.
