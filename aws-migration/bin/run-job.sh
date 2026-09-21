#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Single cron entrypoint for every NutrioBox job.
#   run-job.sh <job-name>
# Activates the venv, sets IST, runs the mapped command from automation/, logs to
# automation/logs/<job>.log with EXIT markers, and alerts on non-zero exit.
#
# Job -> command mapping lives in the case block below. Args match how Task
# Scheduler invoked them (default = the job's normal "yesterday/last-period" run).
# ---------------------------------------------------------------------------
set -uo pipefail

REPO="${REPO:-/opt/nutriobox}"
AUTO="$REPO/automation"
LOGS="$AUTO/logs"
VENV="$REPO/.venv/bin/activate"
export TZ="Asia/Kolkata"

job="${1:-}"
[ -z "$job" ] && { echo "usage: run-job.sh <job-name>"; exit 2; }

mkdir -p "$LOGS"
LOG="$LOGS/${job}.log"

# shellcheck disable=SC1090
source "$VENV"
cd "$AUTO"

# --- map job name -> command ---------------------------------------------
cmd=()
case "$job" in
  refresh-tokens)     cmd=(python refresh_tokens.py) ;;
  daily-data)         cmd=(python daily_data.py) ;;
  kot-daily)          cmd=(python kot_daily.py) ;;
  kot-weekly)         cmd=(python kot_weekly.py) ;;
  kot-monthly)        cmd=(python kot_monthly.py) ;;
  daily-sheet)        cmd=(python daily_sheet.py) ;;
  ratings)            cmd=(python ratings.py) ;;
  delay)              cmd=(python delay_dashboard.py) ;;
  discount-weekly)    cmd=(python discount_weekly.py) ;;
  momos)              cmd=(python momos_weekly.py) ;;
  monthly-sales-fill) cmd=(python monthly_sales_fill.py) ;;
  weekly-sales)       cmd=(python weekly_sales_sync.py) ;;
  weekly-report)      cmd=(python weekly_report.py) ;;
  incentive-delay)    cmd=(python incentive_delay.py) ;;
  incentive-weekly)   cmd=(python incentive_weekly.py) ;;
  incentive-monthly)  cmd=(python incentive_monthly.py) ;;
  monthly-dashboard)  cmd=(python monthly_dashboard.py) ;;
  monthly-resync)     cmd=(python monthly_resync.py) ;;
  monthly-reminder)   cmd=(python monday_reminder.py) ;;
  session-watch)      cmd=(python session_watch.py) ;;
  failure-watch)      cmd=(python failure_watch.py) ;;
  discount-fetch)     cmd=(node "$REPO/scripts/fetch-discount-email.mjs") ;;
  sales-deploy)       cmd=(bash "$REPO/aws-migration/bin/upload-dashboard.sh") ;;
  *) echo "unknown job: $job"; exit 2 ;;
esac

# --- run with logging + exit marker --------------------------------------
{
  echo "Now IST: $(date '+%Y-%m-%d %H:%M:%S%z')"
  echo "RUN: ${cmd[*]}"
} >> "$LOG"

"${cmd[@]}" >> "$LOG" 2>&1
rc=$?
echo "==== EXIT $rc ==== $(date '+%H:%M:%S')" >> "$LOG"

# --- alert on failure (reuse failure_watch's notifier if present) --------
if [ "$rc" -ne 0 ]; then
  echo "[run-job] $job FAILED rc=$rc — see $LOG" >&2
  # Optional: fire an immediate alert. failure_watch.py emails on its own schedule;
  # to alert instantly, uncomment:
  # python failure_watch.py --alert "$job exited $rc" >> "$LOGS/failure_watch.log" 2>&1 || true
fi
exit "$rc"
