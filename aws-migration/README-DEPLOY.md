# Deploy NutrioBox automation to the Ubuntu EC2 — runbook

Follow top to bottom. It moves every repo job off the laptop onto the server,
one safe step at a time. Times are IST. Read ARCHITECTURE.md first for the why.

Legend: **[laptop]** run on your Windows laptop · **[server]** run over SSH on the EC2.

---

## 0. Prerequisites (5 min)

- [server] **RAM check** — headless Chromium (for `refresh_tokens.py`) needs ~1 GB free.
  `free -h`. If the instance is a `t2.micro`/`t3.micro` (1 GB total), add a 2 GB swap file:
  ```bash
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
  `t3.small` (2 GB) or bigger is comfortable and needs no swap.
- [laptop] You can SSH in: `ssh ubuntu@<server-ip>`. Have the `.pem` key handy.
- Outbound internet from the server to Petpooja/Zomato/Swiggy/Google/Supabase/GitHub
  (default EC2 egress allows this).

---

## 1. Copy the repo + secrets to the server (10 min)

The secrets are NOT in git — copy them explicitly. The `browser-profile/` is ~574 MB.

[laptop] (PowerShell, using scp; or use WinSCP/FileZilla for the big folder):
```powershell
# code + this bundle (skip node_modules/.next/.git to keep it small)
scp -r C:\Users\hp\Downloads\Operationsdashboard ubuntu@<server-ip>:/tmp/opsdash

# on the server, move it into place
ssh ubuntu@<server-ip> "sudo mkdir -p /opt/nutriobox && sudo mv /tmp/opsdash/* /opt/nutriobox/ && sudo chown -R ubuntu:ubuntu /opt/nutriobox"
```
Make sure these came across (they're the ones git ignores):
- `/opt/nutriobox/.env.local`
- `/opt/nutriobox/automation/secrets/nutriobox-sa.json`
- `/opt/nutriobox/automation/secrets/tokens.json`
- `/opt/nutriobox/automation/secrets/browser-profile/`  ← the big one; copying it means **no re-login on day one**

> If `scp` chokes on `browser-profile`, zip it first (`Compress-Archive`) and scp the zip, or use `rsync`/WinSCP.

---

## 2. Provision the server (10 min)

[server]
```bash
cd /opt/nutriobox
sudo bash aws-migration/setup.sh
```
This installs Python venv + deps, Playwright Chromium (+ its system libs), Node, Xvfb/VNC,
and creates the log/secret dirs. Re-runnable if anything hiccups.

---

## 3. Verify sessions (5 min)

[server]
```bash
source /opt/nutriobox/.venv/bin/activate
cd /opt/nutriobox/automation
python refresh_tokens.py --check
```
- All `ok` → you're set (the copied profile carried the logins over).
- Anything `LOGGED OUT` → seed it over VNC:
  ```bash
  bash /opt/nutriobox/aws-migration/bin/vnc-login.sh
  ```
  then from the laptop: `ssh -L 5900:localhost:5900 ubuntu@<server-ip>`, open a VNC viewer to
  `localhost:5900`, sign in to each portal, close the browser. Re-run `--check`.

---

## 4. Validate jobs BEFORE scheduling (15 min)

Prove the HTTP clients work on the server without writing anything:
```bash
python kot_daily.py --selftest          # readers healthy, writes nothing
python kot_daily.py --dry-run --date $(date -d yesterday +%F)   # full pull, no write
```
Then run one real job by hand and confirm its sheet/Supabase target updated:
```bash
bash /opt/nutriobox/aws-migration/bin/run-job.sh kot-daily
tail -n 30 /opt/nutriobox/automation/logs/kot-daily.log   # look for ==== EXIT 0 ====
```
Spot-check 2–3 more via `run-job.sh <name>` (names are in `cron/nutriobox-cron`). Fix any
path/arg mismatch now — a couple of jobs may take a `--date`/`--month` flag; compare against
your old `run_*.bat` if a default run isn't right, and tell me so I adjust `run-job.sh`.

---

## 5. Cut over from the laptop (CRITICAL — avoid double-writes)

**Disable the laptop's copies of each job as you enable it on the server, or both will
write the same sheet.**

[laptop] Disable the Windows scheduled tasks:
```powershell
# list them
schtasks /query /fo table | findstr /i NutrioBox
# disable each (repeat per task name), e.g.:
schtasks /change /tn "NutrioBox-KOT-Daily" /disable
schtasks /change /tn "NutrioBox-DailyData-AM" /disable
# ...disable all NutrioBox-* tasks once the server side is verified
```
[laptop] Disable the still-enabled **Cowork** scheduled tasks that overlap (in the desktop
app → Scheduled), e.g. `nutriobox-daily-data-v2`, `weekly-petpooja-*`, `daily-offer-tracker`
(the last only once section B below is sorted). The already-DISABLED Cowork tasks need nothing.

Do this **job-by-job**: enable on server (step 6) → watch one clean run → disable on laptop.

---

## 6. Install the schedule (2 min)

[server] Edit `REPO`/`REPORTS_DIR` at the top of `cron/nutriobox-cron` if your paths differ,
then:
```bash
crontab /opt/nutriobox/aws-migration/cron/nutriobox-cron
crontab -l          # confirm
```
Cron now runs everything in IST. Watch the first morning:
```bash
tail -f /opt/nutriobox/automation/logs/*.log
```

---

## 7. Monitoring

- Per-job logs: `/opt/nutriobox/automation/logs/<job>.log`, each run ends with `==== EXIT n ====`.
- `session-watch` (09:00/15:00) publishes `reports/session-status.json` and emails you before a
  session expires — that's your cue to run `vnc-login.sh` again.
- `failure-watch` (every 4 h) flags any job whose latest exit was non-zero.
- The dashboard's own daily health-check (still on the desktop app for now) will confirm the
  live site matches — you can point it at the server later or retire it.

---

## 8. Loose ends (not blocking the migration)

- **Offer Tracker email (04:09)** — a *separate* Node/Playwright project (not in this repo) plus
  a **dead Apps Script deployment**. To finish it on AWS: (a) redeploy `send_daily_offer_report.gs`
  and capture a live `/exec` URL (the fix from earlier today), (b) get me that project's source so
  I can port it and add the `offer-tracker` line to the crontab. Until then its downstream
  `discount-fetch` has no email to read — today's discount reports are being handled manually.
- **AI health-checks** — optional to move; `session-watch`/`failure-watch` cover the mechanics.

---

## Rollback

Nothing here deletes the laptop setup. To roll back: `crontab -r` on the server and
re-enable the Windows tasks (`schtasks /change /tn "<name>" /enable`). Because you cut over
job-by-job, a problem with one job never affects the others.
