# NutrioBox automation → AWS (Ubuntu) — architecture

Goal: run every scheduled automation on your existing Ubuntu EC2 instance so the
laptop can stay off. Prepared 21 Sep 2026.

## Why this is a clean migration

Your automation was already refactored into the right shape for a headless server:

- **`automation/refresh_tokens.py` is the only component that needs a real browser.**
  It opens Petpooja/Zomato/Swiggy in a Playwright *persistent context*
  (`automation/secrets/browser-profile/`, ~574 MB) and harvests fresh cookies/tokens
  into `automation/secrets/tokens.json`.
- **Every other job is plain HTTP** (`requests` + the Google Sheets API) or Node —
  no browser, no GUI. Those run headless on Linux with zero changes.

So the migration is essentially: copy the repo + secrets to the server, install a
Python venv + Chromium (for the token broker only), translate the Windows Task
Scheduler entries to cron, and seed the login once.

## Target layout on the server

```
/opt/nutriobox/                     # the repo, copied from the laptop
├── automation/                     # all *.py jobs (unchanged)
│   ├── secrets/
│   │   ├── browser-profile/        # copied from laptop → logins transfer, no re-login
│   │   ├── tokens.json
│   │   └── nutriobox-sa.json       # Google service account (Sheets)
│   └── logs/                       # per-job logs (unchanged path)
├── scripts/                        # Node .mjs deploy/fetch helpers (unchanged)
├── .env.local                      # SUPABASE_* / GMAIL_* / GOOGLE_* secrets
└── aws-migration/                  # THIS bundle
    ├── setup.sh                    # one-time provisioning
    ├── bin/
    │   ├── run-job.sh              # cron entrypoint (venv + TZ + logging + alerts)
    │   ├── upload-dashboard.sh     # bash port of auto-deploy.ps1 / upload-dashboard.ps1
    │   └── vnc-login.sh            # headed refresh_tokens.py --login over VNC
    ├── cron/nutriobox-cron         # all schedules in cron (IST)
    ├── systemd/                    # optional: run-job as transient units + timers
    └── nutriobox.env.example       # extra env this bundle needs
```

Nothing about the job code changes. The bundle only adds the Linux plumbing
(venv activation, timezone, cron, logging, session login) around the existing scripts.

## Timezone

Every schedule below is **IST**. Ubuntu EC2 defaults to UTC. We keep the server on
UTC (don't fight it) and put `CRON_TZ=Asia/Kolkata` at the top of the crontab, so the
cron *times* are interpreted as IST. Job code that needs IST already computes it
itself (`timezone(timedelta(hours=5, minutes=30))`), so this only affects when cron fires.

## Sessions & auth (the one manual bit)

- The 574 MB `secrets/browser-profile/` already holds live Petpooja/Zomato/Swiggy
  logins. **Copy it to the server and logins transfer** — no re-login on day one.
- Sessions still expire over time (Petpooja fastest, ~1–3 days). When they do, you
  reconnect to the server over **VNC** and run `bin/vnc-login.sh`, which launches
  `refresh_tokens.py --login` in a real Chromium so you can sign in by hand. This is
  the "occasional interactive re-login" you accepted. `session_watch.py` still emails
  you before things go stale, so you get warning.
- The daily headless `refresh_tokens.py` run (harvests fresh tokens) is scheduled
  before the morning data jobs.

## Job inventory

### A. Repo jobs — migrate as-is (Python/Node, headless)

| Cron (IST) | Job | Command |
|---|---|---|
| 30 3 * * *  | refresh-tokens (headless harvest) | `python refresh_tokens.py` |
| 0 4 * * *   | daily-data AM | `python daily_data.py` |
| 0 16 * * *  | daily-data PM | `python daily_data.py` |
| 15 5 * * *  | KOT daily | `python kot_daily.py` |
| 20 11 * * 1 | KOT weekly (Mon) | `python kot_weekly.py` |
| 30 12 1 * * | KOT monthly (1st) | `python kot_monthly.py` |
| 45 10 * * * | daily sheet | `python daily_sheet.py` |
| 0 6 * * 1   | ratings weekly (Mon) | `python ratings.py` |
| 0 6 * * 3   | delay weekly (Wed) | `python delay_dashboard.py` |
| 0 6 * * 1   | discount weekly (Mon) | `python discount_weekly.py` |
| 15 6 * * 1  | momos weekly (Mon) | `python momos_weekly.py` |
| 0 7 * * 1   | monthly sales fill (Mon) | `python monthly_sales_fill.py` |
| 15 12 * * 1 | weekly sales (Mon) | `python weekly_sales_sync.py` |
| 0 3 * * 3   | weekly report (Wed) | `python weekly_report.py` |
| 0 5 * * 3   | incentive delay (Wed) | `python incentive_delay.py` |
| 30 15 * * 1 | incentive weekly (Mon) | `python incentive_weekly.py` |
| 0 13 1 * *  | incentive monthly (1st) | `python incentive_monthly.py` |
| 15 11 1 * * | monthly dashboard (1st) | `python monthly_dashboard.py` |
| 30 5 3 * *  | monthly resync (3rd) | `python monthly_resync.py` |
| 30 11 1 * * | monthly reminder (1st) | `python monday_reminder.py` |
| 0 9,15 * * * | session watch | `python session_watch.py` |
| 0 8,12,16,20,0,4 * * * | failure watch (every 4h) | `python failure_watch.py` |
| 30 9 * * *  | sales deploy AM | `bin/upload-dashboard.sh` |
| 40 16 * * * | sales deploy PM | `bin/upload-dashboard.sh` |
| 0 5 * * *   | discount fetch | `node scripts/fetch-discount-email.mjs` |

All of these are in this repo and run headless. Exact CLI args for a few jobs are
taken from your `run_*.bat` wrappers where known; `run-job.sh` calls the default
invocation (no `--date` = the job's normal "yesterday/last-period" behaviour), which
matches how Task Scheduler ran them. Verify each once in `--dry-run`/`--selftest`
during cutover (see README-DEPLOY.md).

### B. Loose end — the Offer Tracker email (separate project, NOT in this repo)

The daily **Offer Tracker email** (04:09) is generated by a *separate* Node/Playwright
project that lives outside this repo (`…\Documents\Claude\Scheduled\daily-offer-tracker\`),
and it sends via an Apps Script Web App whose deployment is currently **dead** (see the
work from earlier today). Two things are needed before this one can run on AWS:

1. **Redeploy the Apps Script** `send_daily_offer_report.gs` and capture a working
   `/exec` URL (the fix we discussed — pending your go-ahead).
2. **Bring that offer-tracker project's source into the repo** (or point me at it) so I
   can port it alongside the rest. Until then, its downstream `fetch-discount-email.mjs`
   (which reads the email into the dashboard) has nothing to fetch.

Everything in section A does **not** depend on this, so we migrate A first and treat B
as a follow-on.

### C. Cowork AI health-checks (this task + the evening one)

These are the two daily "health check + auto-fix" agents. They're AI tasks, not
scripts. On the server, `failure_watch.py` + `session_watch.py` already cover the
mechanical parts (endpoint checks, hash compare, session status, alerts). The
richer AI health-check can stay on the laptop/desktop app, or be reduced to a
scripted check — your call once A is stable. It is **not** required for the pipeline
to run.
