# NutrioBox Automation — Setup

One-time setup, ~15 minutes. After this, `kot_daily.py` runs with zero Claude tokens.

Everything lives in `C:\Users\hp\Downloads\Operationsdashboard\automation\`.

---

## Step 1 — Install

```powershell
cd C:\Users\hp\Downloads\Operationsdashboard\automation
pip install -r requirements.txt
python -m playwright install chromium
```

---

## Step 2 — Google service account (this is the big unlock)

This replaces every Name Box / clipboard-paste / "did the paste land one row off?"
hack across 8 of your tasks.

1. Go to <https://console.cloud.google.com/iam-admin/serviceaccounts>
2. Pick (or create) a project → **Create Service Account**
   - Name: `nutriobox-bot` → Create → Done (no roles needed)
3. Click the new account → **Keys** → **Add Key** → **Create new key** → **JSON**
4. Save the downloaded file as:
   `C:\Users\hp\Downloads\Operationsdashboard\automation\secrets\nutriobox-sa.json`
5. Copy the service account's email — it looks like
   `nutriobox-bot@<project>.iam.gserviceaccount.com`
6. **Share these sheets with that email as Editor** (normal Google "Share" button):

   | Sheet | Used by |
   |---|---|
   | [Daily KOT Comparison](https://docs.google.com/spreadsheets/d/1yOYpZBjohebpfpjRIfrDnUNd21bDcFcbt2vem1D_mn8) | `kot_daily.py` (source) |
   | [Sales Data](https://docs.google.com/spreadsheets/d/1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs) | `kot_daily.py` (dest) + the 4 sales tasks |
   | [Weekly KOT Comparison](https://docs.google.com/spreadsheets/d/1eFBNV1bAwXqATegto9k0S2N9KfCGAtyufmbkpbzQX30) | weekly KOT port |
   | [Weekly Sales](https://docs.google.com/spreadsheets/d/1oNCCGX5ntgPW_OYwjWB5LMFhLfPitxzVAMWj95G0qpc) | delay dashboard + Wed report |

> Service-account keys never expire. No consent screen, no 7-day refresh-token
> problem, no OAuth flow in a headless job.

---

## Step 3 — Sign in to Petpooja / Zomato / Swiggy (once)

```powershell
python refresh_tokens.py --login
```

A browser opens with three tabs. Sign in to each, come back, press Enter.
The profile is saved in `secrets/browser-profile/` and persists — you should not
need to do this again for weeks.

Then, daily (and any time a site logs out):

```powershell
python refresh_tokens.py          # headless, ~15 seconds
```

**This is the only browser left in the entire system.** Everything else is plain HTTP.

---

## Step 4 — Prove the client works

```powershell
python kot_daily.py --selftest
```

This re-pulls two values I captured live from Petpooja on 14 Jul 2026 and checks
they still match:

```
  [OK  ] KOT     DLF Phase 2          expected 37, got 37
  [OK  ] Captain Rajinder Nagar       expected 61, got 61

Client is healthy.
```

If this FAILS, Petpooja changed a page — **do not trust any writes.** That's the
whole point of the self-test: it fails loudly instead of writing garbage.

---

## Step 5 — Dry run (writes nothing)

```powershell
python kot_daily.py --dry-run
```

You'll get the full pull plus exactly what it *would* write to both sheets.
Compare against what the Claude task wrote that morning. Run this for 2–3 days.

---

## Step 6 — Go live

Once dry runs match:

```powershell
python kot_daily.py
```

Then schedule it and **disable the Claude `daily-kot-comparison` task**:

```powershell
# 05:10 IST daily — same slot the Claude task used
schtasks /create /tn "NutrioBox-KOT-Daily" /tr `
  "cmd /c cd /d C:\Users\hp\Downloads\Operationsdashboard\automation && python refresh_tokens.py && python kot_daily.py >> logs\kot.log 2>&1" `
  /sc daily /st 05:10
```

---

## What you get

| | Claude task | This script |
|---|---|---|
| Tool calls / LLM turns | ~80 | 0 |
| Sheets cell reads | 27 round trips @ 650ms | 1 API call |
| Writes | clipboard TSV paste, verify, re-paste on failure | 1 batch call, verified |
| Silent-failure modes | stale duplicated tab (hit 21–22 May), paste off by a row | readback assertions abort before damage |
| Runtime | minutes | ~30 seconds |

---

## Safety properties

The script **refuses to write** and exits non-zero if:

- Any outlet reports Captain KOT > Total KOT (impossible → bad scrape)
- Any outlet reports zero KOTs
- The source tab's column A doesn't match the expected outlet order
- The destination block already contains data (re-run protection)
- A readback after writing doesn't match what was sent

This is the anti-stale-copy guard from the SKILL, but enforced in code rather
than by asking an LLM to remember to check.

---

## Next ports (same two modules unlock all of these)

1. **Merge the 4 Monday sales tasks into one script** — they all hit the same
   Petpooja dashboard and the same Sales Data sheet. Biggest single win.
2. `nutriobox-discount-report-daily-upload` — already a complete Python script
   sitting inside a SKILL.md. Just move it to a `.py` and schedule it.
3. `daily-offer-tracker` — the happy path is two HTTP calls (Swiggy GraphQL +
   Zomato REST). Fold the Supabase upload into it and delete the Gmail round-trip.
4. `nutriobox-daily-data-v2` — your most expensive task (2×/day, 100-turn budget).
