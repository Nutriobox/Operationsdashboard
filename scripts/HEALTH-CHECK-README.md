# Automated dashboard health check

Replaces the Cowork/Claude-driven morning check with a standalone Node script
run by Windows Task Scheduler. No Claude in the loop.

| Concern | How it's done |
|---|---|
| Sales dashboard freshness | Content **md5 hash** compare (local export vs live Supabase object), auto-upload on drift |
| Discount codes | Supabase HEAD, then Gmail API fetch if a genuinely new Offer Tracker email exists |
| KOT tab pointers | **Google Sheets API** — newest tab is `properties.index === 0`; republishes the pointer JSON |
| Site render | **Playwright** (headless Chromium) |
| Reporting | Gmail API `messages.send` |

Playwright is used only for the render check. The Sheets work deliberately does
*not* use a browser: scraping Google Sheets needs a logged-in session that
Google invalidates every few weeks, and it fails silently when it does.

## Repo location

The live repo is **`C:\Users\hp\Downloads\Operationsdashboard`**
(remote `github.com/Nutriobox/Operationsdashboard`, branch `main`).

The older `C:\Users\hp\Documents\GitHub\Operationsdashboard` path referenced in
some notes no longer exists — as of 2026-08-22 the only thing under
`Documents\GitHub` is the unrelated `Sukhna-Foods-Operations-Dashboard`.

## Setup — COMPLETE as of 2026-08-22

```
1. DONE - Playwright + Chromium installed (Node v24.16.0)
2. DONE - Google Sheets API enabled on project "NutrioBox Email Sync"
          (nutriobox-email-sync, project number 306307820967)
3. DONE - Re-consented with gmail.readonly + gmail.send + spreadsheets.readonly
4. DONE - Scheduled task NutrioboxHealthCheck, daily 09:35,
          user-level (no admin, no stored password)
5. DONE - Verified: both KOT sheets read via the Sheets API return the same
          gids that the browser reported, so the no-browser path is correct.
```

To re-verify at any time: `node scripts\health-check.mjs --dry-run`

### OAuth caveat

The OAuth app is **External / Testing** with `mayank@nutriobox.com` as the only
test user. Google normally expires Testing-mode refresh tokens after 7 days,
but this one has survived since 2026-07-28, so it isn't biting in practice.
If you ever see sudden `invalid_grant` errors, the permanent fix is switching
the app to **Internal** (available on the nutriobox.com Workspace org, and it
skips Google verification) — not repeatedly re-running the auth script.

## Daily operation

Runs at **09:35 IST**, five minutes after `NutrioboxDailyDeploy`. Emails a
✅/🔧/❌ summary to **`mayank@nutriobox.com`** — the mailbox that owns the
automation, and the same one the Gmail OAuth token belongs to. Override with
`HEALTH_REPORT_TO` in `.env.local` if that ever needs to change.

Exit code is `1` if any ❌ remains, so Task Scheduler's Last Run Result shows a
failure at a glance.

Logs:
- `C:\Users\hp\Desktop\nutriobox-health-check.log` (full history)
- `<repo>\health-check.log` (last run only — readable from a Cowork session,
  since the repo folder is mounted there and the Desktop is not)

## Flags

| Flag | Effect |
|---|---|
| `--dry-run` | Detect only. Never uploads, never emails. |
| `--no-email` | Performs auto-fixes, prints the report, skips the email. |

## Auto-fix rules

**Sales** — uploads only when the live hash differs **and** the local export was
modified today (IST). A stale local export is reported, never uploaded, so an
upstream `nutriobox-daily-data-v2` failure can't be masked.

**Discount** — uploads only when a genuinely newer Offer Tracker email exists.
No email means the upstream `daily-offer-tracker` task is the problem, and the
script says so rather than fabricating a report.

**KOT pointers** — always repoints to the newest existing tab. If that tab isn't
the expected date (i.e. `daily-kot-comparison` never created it), it still
repoints to the newest real tab and flags the gap. It never invents a gid.

## Domain

The site moved from `operationsdashboard.nutriobox.com` to
**`opsdashboard.nutriobox.com`** on 2026-08-22 (Wix DNS + Vercel). The old
hostname no longer has a DNS record and will not come back.

`SITE` at the top of `health-check.mjs` is the single source of truth — the DNS
guard and the render check both derive from it, so a future rename is a one-line
change there.

All other references in the repo were text-only (console messages and one label
in `src/components/DashboardCards.tsx`); they were updated in the same pass, but
`DashboardCards.tsx` needs a deploy before the new label shows on the live site.

## Retiring the old task

Once this has run clean for a few days, delete the
`nutriobox-ops-dashboard-daily-checkin` Cowork scheduled task. Keep a Cowork
session around for *changes* to the dashboard — the script only does the health
check, not feature work.
