# Nutriobox automation — reliability setup

Goal: the jobs run on their own without you babysitting, and you get **told
immediately** (email) on the rare occasions a real re-login is unavoidable —
instead of finding out days later that a sheet stopped filling.

## One-time setup (run each once, in this folder)

1. **`FAILURE-WATCH-SCHEDULE.bat`** — registers the watchdog (`NutrioBox-FailureWatch`,
   every 4 hours). It scans the logs and emails satvik@nutriobox.com the exact fix
   whenever any job's last run failed or a scraper session logged out.
2. **`HARDEN-SCHEDULED-TASKS.bat`** — run this **after** all your `*-SCHEDULE.bat`
   files (and after step 1). Approve the admin prompt. It applies to every
   `Nutri*` task:
   - **catch up missed runs** — if the laptop was off/asleep at the scheduled time,
     the job runs the moment you next power on (no more silently skipped days);
   - **run on battery** — unplugging no longer skips a run;
   - **wake from sleep** to run, then sleep again;
   - **retry twice** (10 min apart) on failure; 2-hour safety cap.

   Re-run `HARDEN-SCHEDULED-TASKS.bat` any time you add a new task.

## Test the alerting

```
python failure_watch.py --test      # sends a test email
python failure_watch.py --dry-run   # scans + prints, sends nothing
```

## The honest limits (nothing fixes these by itself)

- **A fully powered-OFF laptop cannot run or wake itself.** "Catch up missed runs"
  means they run when you next turn it on — not while it's off. If you need them to
  run at the exact time with the laptop off, they have to move to an always-on
  machine (cloud VM / mini-PC). That's the only real way, and it's a separate project.
- **Google / Petpooja / Zomato / Swiggy will occasionally force a re-login** (2FA,
  security checks, bot-detection) that a script can't do unattended. The watchdog
  can't prevent these — but it will email you the moment one happens, with the
  one-line fix (`DELAY-LOGIN.bat` for Google, `TOKENS-LOGIN.bat` for Petpooja etc.),
  so it's a 2-minute occasional task, not daily babysitting.

## Code fixes already applied (14 Sep 2026)

- `daily_sheet.py` — fixed the false "VERIFY FAILED" (gviz-vs-live row offset).
- `sheet_writer.py` `open_book` — retries transient `ERR_CONNECTION_RESET` etc.
- `sheet_browser.py` `login` — no longer crashes if the sign-in window is closed early.
- `discount_weekly.py` — forces UTF-8 output (was crashing on `₹`).

> These live in the `Downloads\Operationsdashboard` clone the jobs run from, and are
> **not git-committed** — if you re-sync that folder from GitHub, port them over.
