#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Bash port of scripts/upload-dashboard.ps1 + the git-push half of auto-deploy.ps1
#
#   1. gzip the newest NutrioBox_Dashboard_*.html and PUT it to Supabase
#      reports/sales-dashboard.html (Content-Encoding: gzip), skipping if the
#      remote already has the same byte count.
#   2. commit + push any code changes (author = mayank@nutriobox.com, or Vercel
#      rejects the deploy).
#
# NOTE: daily_data.py already publishes sales-dashboard.html itself (its Step 7),
# so the upload here is usually a no-op safety net; the git push is the main job.
#
# Env overrides:
#   REPO         (default /opt/nutriobox)
#   REPORTS_DIR  where daily_data.py writes NutrioBox_Dashboard_*.html
#                (default $REPO/exports — set this to match your server)
# ---------------------------------------------------------------------------
set -uo pipefail

REPO="${REPO:-/opt/nutriobox}"
ENVF="$REPO/.env.local"
REPORTS_DIR="${REPORTS_DIR:-$REPO/exports}"
GLOB="NutrioBox_Dashboard_*.html"
BUCKET="reports"
KEYNAME="sales-dashboard.html"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

log(){ echo "[$(date '+%F %T')] [upload] $*"; }

# --- 1. secrets -----------------------------------------------------------
[ -f "$ENVF" ] || { log "MISSING $ENVF"; exit 1; }
set -a; # shellcheck disable=SC1090
source <(tr -d '\r' < "$ENVF"); set +a
SUPA="${NEXT_PUBLIC_SUPABASE_URL:-}"; KEY="${SUPABASE_SERVICE_ROLE_KEY:-}"
[ -z "$SUPA" ] && { log "NEXT_PUBLIC_SUPABASE_URL missing"; exit 1; }
[ -z "$KEY" ]  && { log "SUPABASE_SERVICE_ROLE_KEY missing"; exit 1; }

# --- 2. newest export -> gzip --------------------------------------------
if [ -d "$REPORTS_DIR" ]; then
  latest="$(ls -t "$REPORTS_DIR"/$GLOB 2>/dev/null | head -1 || true)"
else
  latest=""
fi

if [ -n "$latest" ]; then
  gz="$TMP/sales.html.gz"
  gzip -9 -c "$latest" > "$gz"
  gzbytes=$(stat -c%s "$gz")
  log "newest export: $(basename "$latest")  gz=$((gzbytes/1024)) KB"
  if [ "$gzbytes" -gt $((50*1024*1024)) ]; then
    log "ERROR compressed > 50MB — Supabase Free cannot accept it";
  else
    pub="$SUPA/storage/v1/object/public/$BUCKET/$KEYNAME"
    up="$SUPA/storage/v1/object/$BUCKET/$KEYNAME"
    remote=$(curl -sSI -m 30 "$pub" | awk 'tolower($1)=="content-length:"{print $2}' | tr -d '\r')
    if [ "${remote:-0}" = "$gzbytes" ]; then
      log "Supabase already matches ($remote bytes) — skip upload"
    else
      code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$up" \
        -H "apikey: $KEY" -H "Authorization: Bearer $KEY" \
        -H "Content-Type: text/html" -H "Content-Encoding: gzip" \
        -H "Cache-Control: no-cache" -H "x-upsert: true" \
        --data-binary "@$gz" --max-time 90)
      log "upload HTTP $code"
    fi
  fi
else
  log "no $GLOB in $REPORTS_DIR — skipping Supabase upload (daily_data.py may publish directly)"
fi

# --- 3. git code deploy ---------------------------------------------------
cd "$REPO" || exit 0
git config user.email "mayank@nutriobox.com"
git config user.name  "Nutriobox"
git fetch origin >/dev/null 2>&1 || true
if [ -z "$(git status --porcelain)" ]; then
  log "working tree clean — nothing to push"; exit 0
fi
log "committing + pushing code changes"
git add -A
git commit -m "auto-deploy $(date '+%F %T')" >/dev/null 2>&1 || true
if git push origin HEAD >/dev/null 2>&1; then
  log "pushed OK"
else
  log "git push FAILED — check remote/credentials"; exit 1
fi
