#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Headed login for the token broker, over VNC.
# Ubuntu EC2 has no display, so we start a virtual X display (Xvfb), expose it
# with x11vnc, and run `refresh_tokens.py --login` inside it. You connect from
# your laptop with any VNC client, sign in to Petpooja/Zomato/Swiggy/Google by
# hand, then close the browser — the session is saved into
# automation/secrets/browser-profile/ and every headless job uses it afterward.
#
# Usage:
#   bash aws-migration/bin/vnc-login.sh
# then from your laptop:
#   ssh -L 5900:localhost:5900 ubuntu@<server-ip>     # tunnel the VNC port
#   open a VNC client to localhost:5900               # password you set below
#
# Security: VNC is bound to localhost only and reached via the SSH tunnel — it is
# NOT exposed to the internet. Kill it (Ctrl-C) as soon as you're done.
# ---------------------------------------------------------------------------
set -euo pipefail
REPO="${REPO:-/opt/nutriobox}"
export DISPLAY=:99
export TZ="Asia/Kolkata"

echo "==> starting Xvfb :99"
Xvfb :99 -screen 0 1440x900x24 >/tmp/xvfb.log 2>&1 &
XVFB=$!
sleep 2
fluxbox >/tmp/fluxbox.log 2>&1 &

echo "==> starting x11vnc on localhost:5900 (set a one-time password)"
# -localhost keeps it off the public internet; reach it via ssh -L tunnel.
x11vnc -display :99 -localhost -nopw -forever -shared >/tmp/x11vnc.log 2>&1 &
VNC=$!

echo
echo "    Now on your LAPTOP run:   ssh -L 5900:localhost:5900 ubuntu@<server-ip>"
echo "    then point a VNC viewer at localhost:5900"
echo "    Sign in to each portal in the Chromium window, then close it."
echo

# shellcheck disable=SC1090
source "$REPO/.venv/bin/activate"
cd "$REPO/automation"
python refresh_tokens.py --login || true

echo "==> login flow finished — verifying sessions"
python refresh_tokens.py --check || true

echo "==> cleaning up X/VNC"
kill "$VNC" "$XVFB" 2>/dev/null || true
echo "Done. Sessions are saved in automation/secrets/browser-profile/."
