# Playwright cutover runbook — 5 remaining jobs

Audited 27 Aug 2026. Every job below has a **written, compiling port**. What is
missing is the one step that can only happen on this laptop: a headed validation
against the live signed-in Petpooja/Google profile, then registering the Windows
task and disabling the Claude task.

**Do them one at a time.** Each job's validation is independent; a bad cutover on
one should never block the others.

---

## Order to do them in

| # | Job | Script | Risk | Do it |
|---|-----|--------|------|-------|
| 1 | Daily KOT | `kot_daily.py` | low — verified vs 23 Aug ground truth | first; it runs daily so you find problems fast |
| 2 | Weekly KOT | `kot_weekly.py` | low — shares `kot_common.py` with #1 | after #1 survives 2 days |
| 3 | Monthly KOT | `kot_monthly.py` | low — same building blocks | after #2 |
| 4 | Daily Dashboard | `daily_sheet.py` | medium — new scraper, writes 20 cells | after #1 survives 2 days |
| 5 | Momos Weekly | `momos_weekly.py` | medium — writes HTML + git push | last; it is weekly, so slowest to verify |

---

## Preconditions (once, before any cutover)

```powershell
cd C:\Users\hp\Downloads\Operationsdashboard\automation
pip install -r requirements.txt
python -m playwright install chromium
python refresh_tokens.py --check        REM Petpooja must report ok
```

If the Google profile is not signed in, run `DELAY-LOGIN.bat` once and sign in.

---

## 1–3. The three KOT jobs

For each, substitute the right script/date:

```powershell
REM a) readers healthy, writes nothing
python kot_daily.py --selftest

REM b) full pull + write preview, writes nothing
python kot_daily.py --dry-run --date 2026-08-26

REM c) headed live run you watch end-to-end
python kot_daily.py --headed --date 2026-08-26
```

Weekly: `python kot_weekly.py --headed --monday <last-week-Monday>`
Monthly: `python kot_monthly.py --headed --month <YYYY-MM of last month>`

**Only if (c) wrote the correct numbers and the gviz readback passed:**

```powershell
REM d) disable the Claude task FIRST, or both will write the same tab
REM    (Cowork -> scheduled tasks -> toggle off)
REM       daily   -> daily-kot-comparison
REM       weekly  -> kot-comparsion
REM       monthly -> monthly-kot-comparison

REM e) then register the Windows task
KOT-DAILY-SCHEDULE.bat
```

> **Ordering matters.** Disable the Claude task *before* registering the Windows
> one. If both run on the same morning they race for the same Petpooja outlet
> session — that is the "outlet-session collision" that corrupted the 6–12 and
> 13–19 July weeks.

---

## 4. Daily Dashboard (`daily_sheet.py`) — new

```powershell
python daily_sheet.py --selftest                    REM scrape + gates, no sheet access
python daily_sheet.py --dry-run --date 2026-08-26   REM + locates the row, previews B..U
python daily_sheet.py --headed --date 2026-08-26    REM live, watch it
```

What to watch in the dry run:

- `picker shows:` must be the target date. The scraper aborts if not — this is
  the guard against silently writing today's numbers into yesterday's row.
- `target row:` is found by matching the **column-A date label**, not by
  appending after the last filled row.
- `outlets:` — confirm **G = Noida Advant** and **K = Sector 63 Noida** are not
  swapped. This is the single most common error in this sheet.
- The 10 outlet totals must sum to Total Sales; the run refuses to write if not.

Then disable `petpooja-sales-to-gsheet` and register:

```powershell
schtasks /create /tn "NutrioBox-DailySheet" /sc daily /st 10:45 ^
  /tr "cmd /c cd /d C:\Users\hp\Downloads\Operationsdashboard\automation && python daily_sheet.py >> logs\daily_sheet.log 2>&1" /f
```

10:45 keeps it clear of the 04:00 daily-data pull and the ~10:30 slot the Claude
task used.

---

## 5. Momos Weekly (`momos_weekly.py`) — new

```powershell
python momos_weekly.py --selftest
python momos_weekly.py --dry-run --monday 2026-08-24
python momos_weekly.py --headed --monday 2026-08-24     REM writes both HTML copies, no push
```

The script re-checks all **11 reconciliation invariants** before and after the
append, and refuses to write if any fails. It also refuses to append a week that
is already in `weekSpans`, so re-runs are safe.

After a good run, publish:

```powershell
REM either double-click PUSH-momos.bat, or re-run with --publish
python momos_weekly.py --publish --monday 2026-08-24
```

To undo a bad write before pushing:

```powershell
git checkout -- public/nutriobox-momos-dashboard.html nutriobox-momos-dashboard.html
```

Then disable `nutriobox-momos-dashboard--weekly-update-higgsfield` and register:

```powershell
schtasks /create /tn "NutrioBox-Momos-Weekly" /sc weekly /d MON /st 06:15 ^
  /tr "cmd /c cd /d C:\Users\hp\Downloads\Operationsdashboard\automation && python momos_weekly.py --publish >> logs\momos.log 2>&1" /f
```

> **Note on the schema.** `momos_weekly.py` targets the **real** `const D`
> schema (`oSales`, `vVegSales`, …) as rebuilt by commit 2a6cfab. The old task's
> SKILL.md still describes the retired `outlets.*` / `tblVeg` / `variantSplit`
> shape — do not use it as a reference.

---

## Housekeeping — three tasks that should already be off

These are described as "DISABLED — replaced by Playwright" but are still
`enabled: true` and still firing. They duplicate work the Playwright jobs
already do:

| Task | Replaced by | Why it matters |
|------|-------------|----------------|
| `nutriobox-daily-data-v2` | `NutrioBox-DailyData-AM/PM` | ran again 27 Aug 10:35 |
| `nutriobox-ratings-weekly-refresh` | `NutrioBox-Ratings-Weekly` | ran 24 Aug |
| `daily-offer-tracker` | `NutrioBox-OfferTracker` | **two Offer Tracker emails race the 05:00 upload** |

Turn all three off in the Cowork scheduled-tasks list.

---

## Rollback (any job)

1. Re-enable the Claude task.
2. `schtasks /delete /tn "<task name>" /f`
3. For Momos only, if a bad file was committed but not pushed:
   `git reset --hard HEAD~1`
