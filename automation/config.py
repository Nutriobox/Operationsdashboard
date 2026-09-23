"""
Central config for all NutrioBox automation scripts.
Everything that was duplicated across 16 SKILL.md files lives here once.
"""
from pathlib import Path

ROOT = Path(__file__).parent
SECRETS = ROOT / "secrets"
LOGS = ROOT / "logs"

TOKENS_FILE = SECRETS / "tokens.json"
SERVICE_ACCOUNT_FILE = SECRETS / "nutriobox-sa.json"

# The repo's existing .env.local already holds SUPABASE_* and GMAIL_* — reuse it.
ENV_LOCAL = ROOT.parent / ".env.local"

PETPOOJA_BASE = "https://billing.petpooja.com"

# ---------------------------------------------------------------------------
# Outlets
# ---------------------------------------------------------------------------
# `name` must match Petpooja's restaurant_name EXACTLY (including the odd
# spacing) — several CSV joins depend on it.
OUTLETS = {
    349767: "NutrioBox ( DLF Phase 2)",
    159181: "NutrioBox ( Rajinder Nagar)",
    136183: "NutrioBox ( Sector 63 Noida )",
    62697:  "NutrioBox (Dwarka)",
    19652:  "NutrioBox (Janakpuri)",
    16011:  "NutrioBox (Karkardooma)",
    80991:  "NutrioBox (Noida)",
    9960:   "NutrioBox (Prashant Vihar)",
    369621: "NutrioBox (Sector 15, Gurugram)",
    62695:  "NutrioBox (Shivalik)",
}

SHORT = {
    349767: "DLF Phase 2",
    159181: "Rajinder Nagar",
    136183: "Sector 63 Noida",
    62697:  "Dwarka",
    19652:  "Janakpuri",
    16011:  "Karkardooma",
    80991:  "Noida",
    9960:   "Prashant Vihar",
    369621: "Sector 15 Gurugram",
    62695:  "Shivalik",
}

# ---------------------------------------------------------------------------
# KOT comparison
# ---------------------------------------------------------------------------
# Sector 63 Noida (136183) and HO (89083) are NOT in the KOT sheets.
KOT_OUTLETS = [349767, 159181, 62697, 19652, 16011, 80991, 9960, 369621, 62695]

# SOURCE sheet: one tab per day. Outlets down column A (rows 2-10), row 11 = TOTAL.
KOT_SOURCE_SHEET_ID = "1yOYpZBjohebpfpjRIfrDnUNd21bDcFcbt2vem1D_mn8"
KOT_SOURCE_ROW = {          # outlet_id -> row in the dated source tab
    349767: 2,
    159181: 3,
    62697:  4,
    19652:  5,
    16011:  6,
    80991:  7,
    9960:   8,
    369621: 9,
    62695:  10,
}
KOT_SOURCE_TOTAL_ROW = 11

# DESTINATION: "Sales Data" workbook, tab "Daily KOT Comparsion".
# (The misspelling is in the real sheet. Do not "fix" it.)
SALES_DATA_SHEET_ID = "1liC4dGXRnahACXdxI3lbxi-BbE2I7Jb4C49a2R0OiCk"   # native Google Sheet copy (2026-09-23); old .xlsx was 1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs
KOT_DEST_TAB = "Daily KOT Comparsion"

# Destination is a wide layout: outlets across columns, 3 rows per date block.
KOT_DEST_COL = {            # outlet_id -> column letter
    9960:   "C",   # Prashant Vihar
    19652:  "D",   # Janakpuri
    16011:  "E",   # Karkardooma
    62697:  "F",   # Dwarka
    62695:  "G",   # Shivalik
    80991:  "H",   # Noida
    159181: "I",   # Rajinder Nagar
    349767: "J",   # DLF Phase 2
    369621: "K",   # Sector 15 Gurugram
}
KOT_DEST_TOTAL_COL = "L"
KOT_DEST_FIRST_BLOCK_ROW = 2      # block k starts at row 2 + 3*(k-1)
KOT_DEST_BLOCK_HEIGHT = 3
KOT_DEST_METRIC_LABELS = ["Total KOT", "Captain App KOT", "Captain App%"]

KOT_WEEKLY_SHEET_ID = "1eFBNV1bAwXqATegto9k0S2N9KfCGAtyufmbkpbzQX30"

# Weekly ("kot-comparsion") and monthly ("monthly-kot-comparison") both write ONE
# tab per period into their own sheet — outlets down column A (rows 2-10, same
# order/tokens as the daily source), B = Total Dine In/Pick Up KOT, C = Captain
# App KOT, D = coverage formula, row 11 = TOTAL. Unlike the daily task they do NOT
# mirror into the "Sales Data" workbook, and A1 is an "Outlets" header (never
# overwritten). See kot_weekly.py / kot_monthly.py (shared logic in kot_common.py).
KOT_MONTHLY_SHEET_ID = "1TFCNxjX_0AGV2t2fkK_KzCMf3W9uMdSdVGbVB7_Nofw"

# ---------------------------------------------------------------------------
# Petpooja report ids (reference only — the client derives them from the page)
# ---------------------------------------------------------------------------
# Custom reports are served by POST /custom_reports/get_data_query/{group}/{report}.
# Filter inputs on view_report/{view_id} are id'd re_filter_filed_{group}_{report}_{i}_{from|to},
# so petpooja.py reads group/report straight off the page instead of hard-coding them.
REPORT_CAPTAIN_PERFORMANCE = 27   # -> get_data_query/1/19
REPORT_ADDONS = 31                # -> get_data_query/1/23
REPORT_ALL_RESTAURANT_SALES = 9   # -> get_data_query/1/3

# KOT order types (multi-select on /items/kot_list/)
ORDER_TYPE_DELIVERY = "1"
ORDER_TYPE_PICKUP = "2"
ORDER_TYPE_DINEIN = "3"

# ---------------------------------------------------------------------------
# Supabase / dashboard
# ---------------------------------------------------------------------------
SUPABASE_PROJECT = "jkzremlkrxhhshqouudk"
SUPABASE_PUBLIC = f"https://{SUPABASE_PROJECT}.supabase.co/storage/v1/object/public/reports"
# NOTE (2026-08-20): the custom domain is `opsdashboard`, not
# `operationsdashboard` — the latter has no DNS record in Wix and returns
# NXDOMAIN, which silently broke ratings.py's API_RATINGS call.
DASHBOARD_URL = "https://opsdashboard.nutriobox.com"

# ---------------------------------------------------------------------------
# Known-good values, captured live from Petpooja on 14 Jul 2026.
# Used by `python kot_daily.py --selftest` to prove the HTTP client still works.
# ---------------------------------------------------------------------------
SELFTEST = {
    "business_date": "2026-07-13",
    "kot": {349767: 37},        # DLF Phase 2, Dine In + Pick Up
    "captain": {159181: 61},    # Rajinder Nagar
}


# --- one-job-at-a-time lock on the shared browser profile (2026-09-23) -------
# See profile_lock.py. Wraps Playwright so concurrent jobs queue instead of
# crashing each other when the laptop wakes and fires all missed tasks at once.
try:
    import profile_lock as _profile_lock
    _profile_lock.install(SECRETS / "browser-profile")
except Exception as _e:  # never let the lock break a job
    print(f"[profile-lock] not installed: {_e}")
