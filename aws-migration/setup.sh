#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# NutrioBox automation — one-time Ubuntu provisioning
# Run once on the EC2 box after copying the repo to /opt/nutriobox.
#   sudo bash aws-migration/setup.sh
# Idempotent: safe to re-run.
# ---------------------------------------------------------------------------
set -euo pipefail

REPO="${REPO:-/opt/nutriobox}"
PYBIN="${PYBIN:-python3}"
RUN_USER="${SUDO_USER:-$(whoami)}"

echo "==> NutrioBox setup: repo=$REPO  user=$RUN_USER"
cd "$REPO"

# --- 1. OS packages -------------------------------------------------------
echo "==> apt packages"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y
sudo apt-get install -y \
  python3 python3-venv python3-pip \
  git curl ca-certificates gzip \
  nodejs npm \
  xvfb x11vnc fluxbox        # xvfb+vnc used ONLY for refresh_tokens.py --login
# (novnc/websockify optional — install if you prefer browser-based VNC)
sudo apt-get install -y novnc websockify || echo "   (novnc optional — skipped)"

# --- 2. Python venv + deps ------------------------------------------------
echo "==> python venv"
if [ ! -d "$REPO/.venv" ]; then
  "$PYBIN" -m venv "$REPO/.venv"
fi
# shellcheck disable=SC1091
source "$REPO/.venv/bin/activate"
pip install --upgrade pip wheel
pip install -r "$REPO/automation/requirements.txt"

# --- 3. Playwright Chromium (for refresh_tokens.py only) ------------------
echo "==> playwright chromium + system deps"
python -m playwright install --with-deps chromium

# --- 4. Node deps for scripts/*.mjs (if a package.json exists) ------------
if [ -f "$REPO/package.json" ]; then
  echo "==> npm install"
  (cd "$REPO" && npm install --omit=dev)
fi

# --- 5. Directories + permissions ----------------------------------------
mkdir -p "$REPO/automation/logs" "$REPO/automation/secrets"
chmod 700 "$REPO/automation/secrets" || true
chmod +x "$REPO"/aws-migration/bin/*.sh || true

# --- 6. Sanity: secrets present ------------------------------------------
echo "==> checking secrets"
missing=0
for f in .env.local automation/secrets/nutriobox-sa.json; do
  if [ ! -f "$REPO/$f" ]; then echo "   MISSING: $f"; missing=1; fi
done
if [ ! -d "$REPO/automation/secrets/browser-profile" ]; then
  echo "   NOTE: automation/secrets/browser-profile not found —"
  echo "         copy it from the laptop, or run bin/vnc-login.sh to create it."
fi
[ "$missing" = 1 ] && echo "   ^ copy the missing files from the laptop before scheduling."

# --- 7. Timezone note -----------------------------------------------------
echo "==> server timezone is: $(timedatectl show -p Timezone --value 2>/dev/null || date +%Z)"
echo "    (we keep UTC and set CRON_TZ=Asia/Kolkata in the crontab — leave it as-is)"

echo
echo "==> Done. Next:"
echo "    1) Confirm secrets are in place (.env.local, automation/secrets/*)."
echo "    2) Seed/verify sessions:  source .venv/bin/activate && cd automation && python refresh_tokens.py --check"
echo "       (if logged out:        bash aws-migration/bin/vnc-login.sh )"
echo "    3) Dry-run a job:         python kot_daily.py --selftest"
echo "    4) Install cron:          crontab aws-migration/cron/nutriobox-cron  (edit REPO path first if not /opt/nutriobox)"
