# NutrioBox Vehicle Monitoring — Daily Automation

This runs **on your PC** and, once a day, pulls OneLap data, builds the report, updates the
website's dashboard (date-filter history), and emails you the Excel. No passwords ever leave
your machine.

## What it produces
- `public/vehicle-monitoring-data.json` — one entry per day; the dashboard's date filter reads this.
- `reports/Vehicle_Movement_Report_<date>.xlsx` — the filled movement sheet (one tab per vehicle).
- A git commit + push, so `opsdashboard.nutriobox.com/dashboard/vehicle-monitoring` updates.
- An email with the Excel attached.

## One-time setup

1. **Install Python 3** (if not already) from python.org, and the two libraries:
   ```
   pip install requests openpyxl
   ```

2. **Put these files in** `C:\Users\hp\Downloads\Operationsdashboard\automation\vehicle_report\`:
   - `vehicle_report.py`
   - `vehicle_movement_template.xlsx`
   - `vehicle_report_config.example.py`
   - `RUN-vehicle-report.bat`

3. **Create your config:** copy `vehicle_report_config.example.py` to **`vehicle_report_config.py`**
   and fill in:
   - Your OneLap email + password (same as web.onelap.in).
   - `REPO_DIR` (already set to your repo path).
   - Gmail sender + an **App Password** (myaccount.google.com/apppasswords) and recipient(s).
   Leave `SMTP_USER = None` if you don't want email.

4. **Test it** — double-click `RUN-vehicle-report.bat`. It should log in, process each vehicle,
   write the Excel, update the JSON, push, and email. First run publishes the new dashboard.

## Schedule it daily (Windows Task Scheduler)
1. Open **Task Scheduler** → **Create Task**.
2. General: name it "NutrioBox Vehicle Report". Check "Run whether user is logged on or not".
3. Triggers → New → Daily → set time to **8:00 PM** (after routes finish). OK.
4. Actions → New → Program/script: `RUN-vehicle-report.bat`
   Start in: the `...\automation\vehicle_report` folder.
5. Save. Done — it runs every evening.

You can also generate a past day on demand:  `RUN-vehicle-report.bat 2026-08-11`

## Notes
- Vehicles that drove < 5 km are skipped as "no run".
- Stops within ~1.8 km of a known NutrioBox outlet are named as that outlet; others show their
  locality with "(not a listed outlet)" — tell Claude the real names to add them to the map in
  `vehicle_report.py` (the `OUTLETS` dict).
- Keep `vehicle_report_config.py` out of git (it holds your password). Add these lines to
  `.gitignore` (the setup already does this for you):
  ```
  automation/vehicle_report/vehicle_report_config.py
  reports/
  ```
