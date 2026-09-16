# Weekly delay dashboard — Playwright-era port

Replaces the Cowork task `nutriobox-weekly-delay-dashboard` (Wed 06:00 IST).
No Claude tokens. The sheet is read with **Playwright**, driving the same
persistent profile `refresh_tokens.py` maintains; the HTML is edited by
deterministic Python; the file is upserted to Supabase with `curl`, which is what
updates the live site.

| | Claude task | `delay_dashboard.py` |
|---|---|---|
| Sheet read | Claude-in-Chrome + `gviz` | Playwright + `gviz`, same persistent profile as the other jobs |
| Driver | Claude, per run | plain Python, unattended |
| Wrong-tab fallback | guarded by prompt | Guard A, enforced in code, both readers |
| Reruns | re-does the work | detects the week is already present and exits 0 |
| Partial data | possible | Guard C aborts before writing anything |
| Cost | tokens per run | zero |

**Two readers.** `--reader playwright` (the default, what the scheduled job uses)
and `--reader sheets` (the Google Sheets API, via `secrets/nutriobox-sa.json`).
`--reader both` runs the pair and refuses to write unless they agree
cell-for-cell. The self-test uses `both`, so every check validates the browser
path against an independent source — if `gviz` ever falls back to the wrong tab,
the two disagree loudly instead of silently appending another week's numbers.

---

## One-time setup

**Step 1 — sign the profile into Google.** Double-click `DELAY-LOGIN.bat`,
sign in to the account that can see the Weekly Sales sheet, close the window.
The profile lives in `secrets/browser-profile/` and normally stays signed in for
weeks. This is the only manual step, and the only thing that can rot.

**Step 2 — deps** (already installed if the daily-data job runs):

```powershell
cd C:\Users\hp\Downloads\Operationsdashboard\automation
pip install -r requirements.txt
python -m playwright install chromium
```

The service-account key (`secrets/nutriobox-sa.json`) is already in place and is
only used by `--reader sheets` / `--reader both` for cross-checking. The job does
not need it to run.

---

## Status — LIVE as of 2026-08-20

Windows task `NutrioBox-Delay-Weekly`, Wednesdays 06:00, next run 26 Aug.
The Cowork task `nutriobox-weekly-delay-dashboard` was disabled the same day.

Verified before go-live:

- Self-test: 10/10 against the dashboard, plus 10/10 `playwright vs sheets` cross-check
- Dry run with `--reader both`: both readers agree, read path verified
- Replayed 8 weeks of history (Jun 22 → Aug 16) through the append path and got a
  file **byte-identical** to the real dashboard — 19,424 bytes, same md5
- `publish()` smoke-tested against a scratch Supabase object, verified, cleaned up

**Watch the first live run on 26 Aug** (`logs\delay.log`). Note the Windows task
is "Interactive only" — it will not fire if the laptop is off, asleep, or logged
out at 06:00.

---

## Rollout

**1. Self-test — double-click `DELAY-1-SELFTEST.bat`**

Re-fetches the week the dashboard *already ends with* (`Aug 10-16`) and compares
it against what the Claude task wrote last Wednesday:

```
  [OK  ] DLF - Phase 2      dashboard [198, 28.57, 18, 2.6]  sheet [198, 28.57, 18, 2.6]
  [OK  ] Rajinder Nagar     dashboard [253, 31.16, 29, 3.57] sheet [253, 31.16, 29, 3.57]
  ...
  Client is healthy.
```

Ten OKs means the tab naming, the outlet labels and the T–W columns are all
still right. Any FAIL means the sheet moved — **do not go live.**

Unlike a hard-coded self-test this one never goes stale: it re-anchors on
whatever week the dashboard currently ends with.

**2. Dry run — double-click `DELAY-2-DRYRUN.bat`**

Prints the full week next to the previous one, plus the standout outlet, and
writes nothing. Before Wed 26 Aug this will correctly abort with Guard A
(`Aug 17 - Aug 23, 2026` doesn't exist in the sheet yet) — that is the guard
working, not a failure. Run it once the week is in the sheet.

**3. Go live.** Once the dry run looks right:

```powershell
schtasks /create /tn "NutrioBox-Delay-Weekly" ^
  /tr "cmd /c C:\Users\hp\Downloads\Operationsdashboard\automation\run_delay.bat" ^
  /sc weekly /d WED /st 06:00
```

Then **disable the Cowork task `nutriobox-weekly-delay-dashboard`** so the two
don't both append the same week.

> `incentive-delay-metrics-weekly-wed` (Wed 07:09) reads the updated dashboard
> and is deliberately left on Claude. It runs an hour later, so the 06:00 job
> still lands first — no change needed there.

---

## Usage

```powershell
python delay_dashboard.py --login                  # sign the profile into Google
python delay_dashboard.py --selftest --reader both # prove both readers agree
python delay_dashboard.py --dry-run                # fetch + print, write nothing
python delay_dashboard.py                          # live (Playwright)
python delay_dashboard.py --week 2026-08-10        # a specific week (pass its MONDAY)
python delay_dashboard.py --no-publish             # update files, skip Supabase
python delay_dashboard.py --reader sheets          # API instead of the browser
```

If a run dies with **"not signed in to Google"** or **"gviz returned HTML"**, the
profile has been logged out: run `DELAY-LOGIN.bat` and re-run. If it dies with
**"profile is locked"**, another job (`refresh_tokens.py`, `daily_data.py`) is
holding `secrets/browser-profile` — wait and retry. The 06:00 Wednesday slot is
deliberately clear of the 04:00/16:00 daily-data runs.

Log: `logs\delay.log`. A timestamped backup of the previous HTML is kept next to
the primary file as `nutriobox_delay_dashboard_v3.html.bak-YYYYMMDD`.

## Guards

Ported straight from the SKILL, because each one caught a real bug:

- **Guard A** — the target tab must exist, matched exactly. Never fuzzy-match;
  `gviz` used to return a *different* sheet's data for a near-miss name.
- **Guard B** — the new week must differ from the last week already in the
  dashboard. All-identical means a fallback read, not a quiet week.
- **Guard C** *(new)* — all 10 outlets must be found and all 40 values must
  parse. Blank, `-` and `#DIV/0!` are errors, never zeros. A partial week is
  never appended.

Plus the Step 4 file checks: `weeks` length must equal every outlet's data
length, the file must end `</html>`, and the two local copies must be
byte-identical before publish.

## Files it touches

```
C:\Users\hp\Downloads\NutrioBox_Reports\nutriobox_delay_dashboard_v3.html              (primary)
C:\Users\hp\Downloads\NutrioBox_Reports\Application\nutriobox_delay_dashboard_v3.html  (deployed copy)
Supabase reports/delay-dashboard.html                                                  (plain HTML, NOT gzipped)
```

Note the deploy copy lives under `NutrioBox_Reports\Application\`, not
`C:\Users\hp\Downloads\Application\` — the ops-dashboard runbook has the older
path written down.
