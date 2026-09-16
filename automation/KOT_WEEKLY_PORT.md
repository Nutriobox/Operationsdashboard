# Weekly KOT Comparison → Playwright + HTTP (port of `kot-comparsion`)

Moves the weekly KOT task off Claude, reusing the daily port's building blocks
(`petpooja.py` + `browser_export.py` + `sheet_writer.py`). Only the date window,
sheet id, and tab naming differ — the shared pull/write logic lives in
`kot_common.py`.

## What runs

```
petpooja.py       kot_count()            Total Dine In/Pick Up KOT — HTTP POST /items/klist/
browser_export.py scrape_captain_kots()  Captain App KOT — Playwright (view_report/27 is JS-rendered)
kot_common.py     pull/sanity/write_source  shared with kot_monthly.py
kot_weekly.py     orchestrator           --selftest / --dry-run / --headed / live
```

Pipeline = pull all 9 outlets for the week → sanity gates (Captain ≤ Total, no
zero outlets) → duplicate the newest (leftmost) tab into the new week tab and
write **B2:C10 only** → read every write back through gviz and compare.

## Window & naming (matches the SKILL exactly)

- Target = the most recently **completed** Mon–Sun week.
- Both filters span **[week-Monday 13:00:00 → next-Monday 13:00:00)**.
  KOT format `15 Jun 2026 13:00:00`; Captain format `2026-06-15 13:00:00`.
- Tab name `"<startDay><ord> <Month> - <endDay><ord> <Month>"`, e.g.
  `17th August - 23rd August` (each side keeps its own month across a crossing).

## Differences from the daily port

- **Source-only.** There is no "Sales Data" mirror — the weekly job writes just
  the Weekly KOT sheet (`config.KOT_WEEKLY_SHEET_ID`).
- **A1 is never written.** On the weekly sheet A1 is the `Outlets` header; the
  week lives in the tab name. `write_source(..., write_a1=False)`.
- Everything else (duplicate-newest-on-the-left, column-A token check before
  writing, gviz readback) is identical.

## Validate on the laptop before cutover (needs the signed-in Google profile)

The pull is fully verifiable headless; the **writes can only be exercised where
the browser profile is signed in to Google** (this laptop).

1. Session + reader liveness:
   ```
   python refresh_tokens.py --check          REM Petpooja must be ok
   python kot_weekly.py --selftest           REM both readers healthy
   ```
   If `--selftest` says the Google session isn't signed in, run `DELAY-LOGIN.bat`
   once (sign in as mayank@nutriobox.com, close the window).
2. Dry-run the real week and eyeball the 18 numbers:
   ```
   python kot_weekly.py --dry-run
   ```
3. **Watch it write, headed**, for a week that's genuinely missing (or re-fill
   the latest — writes are idempotent, same numbers land):
   ```
   python kot_weekly.py --headed --monday 2026-08-17
   ```
   Confirm a `17th August - 23rd August` tab is created at the LEFT with B2:C10
   filled; D (coverage) and row 11 (TOTAL) recalc. The run self-verifies via gviz
   and aborts on any mismatch, so a clean exit means the numbers landed.
4. From then on the normal run (last completed week, headless) is just:
   ```
   python kot_weekly.py
   ```

## Go live

Only after step 3 passes:

1. Disable the Claude task so the two don't both write:
   (Cowork) disable scheduled task **kot-comparsion**.
2. Register the Windows job:
   ```
   KOT-WEEKLY-SCHEDULE.bat        REM creates NutrioBox-KOT-Weekly, Mon 11:20 IST
   ```

`kot_weekly.py` refuses to write if column A isn't the 9 outlets in order, and
re-reads every value it writes, so an accidental double-run is safe (it just
re-lands the same numbers). Adjust the Monday time in `KOT-WEEKLY-SCHEDULE.bat`
if it ever clashes with another Petpooja job.
