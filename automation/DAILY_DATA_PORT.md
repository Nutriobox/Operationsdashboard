# Sales Item Dashboard → Playwright + HTTP (port of `nutriobox-daily-data-v2`)

This ports your most expensive Claude task off Claude. The normal run is
deterministic Python + **one** Playwright step (the CSV export). Claude API is
wired in as a **dormant** fallback — it does nothing until you add a key.

## What runs

```
refresh_tokens.py   (already yours)  keeps Petpooja logged in -> secrets/tokens.json
browser_export.py   NEW  Playwright: click Export, grab the S3 CSV  (the only browser step)
petpooja.py         +addons()  +pos_dashboard_total()   pure HTTP
dashboard_build.py  NEW  DAILY_DATA byte-slice rebuild + gzip + Supabase publish (no browser, no LLM)
claude_assist.py    NEW  self-heal / anomaly note / reconcile judgment — OFF until ANTHROPIC_API_KEY is set
daily_data.py       NEW  orchestrator: --selftest / --dry-run / live
```

Pipeline = the SKILL, enforced in code: hour-aware target date → double CSV
export → dedupe to invoice level → morning POS reconciliation → all-10 addons →
validation gates → DAILY_DATA rebuild (drops target biz-day, **keeps** its
<08:00 late-night tail) → **prev-day sales must be identical or it aborts** →
write once → gzip + upsert to Supabase, verified by md5.

## Already verified (in the sandbox, against your real 135 MB export)

- Full rebuild runs in ~4s; drops the target day's rows, re-appends, and
  **prev-day biz sales stayed identical (₹755,935 → stable)**.
- Byte markers correct: `DAILY_DATA=[{…}]` start and `</html>` end both asserted.
- All modules compile and import; Claude assist correctly reports **dormant**.

## You must validate on the laptop (needs your live Petpooja session — I can't from here)

1. `pip install -r requirements.txt` then `python -m playwright install chromium`
2. `python refresh_tokens.py --check`  → Petpooja must be `ok`
3. **Self-test** (writes nothing):
   ```
   python daily_data.py --selftest
   ```
   Confirms the session is alive, the addon pull matches Petpooja's own Total
   row, and the dashboard marker parses. If it fails, Petpooja changed a page —
   do NOT trust writes (that's the point).
4. **Dry run** (full pull + rebuild in a temp dir, writes nothing live):
   ```
   python daily_data.py --dry-run                # auto morning/afternoon by clock
   python daily_data.py --dry-run --date 2026-08-16 --mode morning
   python daily_data.py --dry-run --headed       # watch the export browser once
   ```
   Compare the printed target-day sales + per-outlet counts against what the
   Claude task wrote that morning. Do this 2–3 days.

The two Petpooja-facing pieces most likely to need a small tweak on first real
run: the **Export button selector** in `browser_export.py::_click_export` and
the **POS dashboard total** regex in `petpooja.py::pos_dashboard_total`. The
addon parser reuses your proven `custom_report` path and self-verifies against
the page Total, so it fails loudly rather than writing garbage.

## Go live

```
python daily_data.py            # writes the local HTML + publishes to Supabase
```

Schedule twice daily (same slots as the Claude task) and then disable the Claude
`nutriobox-daily-data-v2` task:

```
schtasks /create /tn "NutrioBox-DailyData-AM" /sc daily /st 04:00 /tr ^
 "cmd /c cd /d C:\Users\hp\Downloads\Operationsdashboard\automation && python refresh_tokens.py && python daily_data.py >> logs\daily_data.log 2>&1"

schtasks /create /tn "NutrioBox-DailyData-PM" /sc daily /st 16:00 /tr ^
 "cmd /c cd /d C:\Users\hp\Downloads\Operationsdashboard\automation && python refresh_tokens.py && python daily_data.py >> logs\daily_data.log 2>&1"
```

The 09:35 / 16:40 check-in tasks stay as a harmless backstop.

## Turning on the Claude API later (optional)

Add to `automation/.env` (or the repo `.env.local`):

```
ANTHROPIC_API_KEY=sk-ant-...
# optional: CLAUDE_ASSIST_MODEL=claude-sonnet-5
```

Then it activates in exactly three spots, all off the happy path:
self-heal a broken parser, write a one-line anomaly note, and judge the morning
POS-vs-export mismatch. With no key, each falls back to its fixed rule.
```
python claude_assist.py     # prints: claude assist available: True/False
```
