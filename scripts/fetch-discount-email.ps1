# Daily 6 AM Gmail fetcher for the NutrioBox Daily Offer Tracker.
#
# Triggered by Windows Task Scheduler at 06:00 IST. Steps:
#   1. Read OAuth credentials + refresh token from .env.local.
#   2. Exchange the refresh token for a short-lived access token.
#   3. Query Gmail for today's "NutrioBox Offer Tracker" emails.
#   4. Pick the latest one (in case multiple were sent).
#   5. Extract the HTML body.
#   6. Wrap with the same styles as the in-browser scrape.
#   7. PUT it to Supabase Storage as discount-codes-YYYY-MM-DD.html.
#   8. The Operations Dashboard's /api/discount-codes-latest endpoint will
#      automatically pick this up as the most recent date.
#
# Logs everything to %USERPROFILE%\Desktop\nutriobox-deploy.log so you can
# see what happened the next morning.

$ErrorActionPreference = 'Continue'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile     = Join-Path $ProjectRoot '.env.local'
$LogFile     = Join-Path $env:USERPROFILE 'Desktop\nutriobox-deploy.log'

function Log {
    param([string]$msg, [string]$level = 'INFO')
    $line = "[{0}] [{1}] [discount] {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $level, $msg
    $line | Tee-Object -FilePath $LogFile -Append | Out-Null
    Write-Host $line
}

Log "---- fetch-discount-email starting ----"

if (-not (Test-Path $EnvFile)) {
    Log "Missing .env.local at $EnvFile" 'ERROR'
    exit 1
}

# Parse .env.local
$envVars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.+?)\s*$') {
        $envVars[$matches[1]] = $matches[2]
    }
}

$clientId     = $envVars['GMAIL_CLIENT_ID']
$clientSecret = $envVars['GMAIL_CLIENT_SECRET']
$refreshToken = $envVars['GMAIL_REFRESH_TOKEN']
$supabaseUrl  = $envVars['NEXT_PUBLIC_SUPABASE_URL']
$secretKey    = $envVars['SUPABASE_SERVICE_ROLE_KEY']

foreach ($k in @('GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET', 'GMAIL_REFRESH_TOKEN',
                 'NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY')) {
    if (-not $envVars[$k]) {
        Log "Missing $k in .env.local" 'ERROR'
        exit 1
    }
}

# Today's date in IST (the report is timestamped in IST, and the scheduled
# task runs at 6 AM local time which is IST on this machine).
$todayIst = (Get-Date).ToUniversalTime().AddHours(5.5).ToString('yyyy-MM-dd')
Log "Looking for today's report ($todayIst)..."

# 1. Get a fresh access token
Log "Refreshing access token..."
try {
    $tokenResp = Invoke-RestMethod -Method Post `
        -Uri 'https://oauth2.googleapis.com/token' `
        -Body @{
            client_id     = $clientId
            client_secret = $clientSecret
            refresh_token = $refreshToken
            grant_type    = 'refresh_token'
        } `
        -ContentType 'application/x-www-form-urlencoded'
    $accessToken = $tokenResp.access_token
} catch {
    Log "Token refresh failed: $_" 'ERROR'
    exit 1
}
Log "Got access token."

# 2. Query Gmail for today's tracker email
# We use newer_than:1d to limit the search; in unusual cases (running late)
# this catches emails from the previous calendar day too, which is what we
# want since the report timestamps run in IST.
$query = 'from:"NutrioBox Offer Tracker" newer_than:1d'
$listUrl = "https://gmail.googleapis.com/gmail/v1/users/me/messages?q=$([uri]::EscapeDataString($query))&maxResults=10"

try {
    $listResp = Invoke-RestMethod -Method Get -Uri $listUrl `
        -Headers @{ Authorization = "Bearer $accessToken" }
} catch {
    Log "Gmail list failed: $_" 'ERROR'
    exit 1
}

if (-not $listResp.messages -or $listResp.messages.Count -eq 0) {
    Log "No NutrioBox Offer Tracker emails in the last 24 hours. Skipping." 'WARN'
    Log "---- fetch-discount-email finished (no email) ----"
    exit 0
}

Log "Found $($listResp.messages.Count) candidate messages. Picking the most recent..."

# 3. Pick the most recent message that mentions today's date
$pickedMessage = $null
$pickedDateText = ''

foreach ($m in $listResp.messages) {
    $msgUrl = "https://gmail.googleapis.com/gmail/v1/users/me/messages/$($m.id)?format=full"
    try {
        $msg = Invoke-RestMethod -Method Get -Uri $msgUrl `
            -Headers @{ Authorization = "Bearer $accessToken" }
    } catch {
        Log "Failed to fetch message $($m.id): $_" 'WARN'
        continue
    }

    # The first message returned by Gmail list is the newest. Take it.
    $pickedMessage = $msg
    break
}

if (-not $pickedMessage) {
    Log "Couldn't fetch any candidate message." 'ERROR'
    exit 1
}

# 4. Extract HTML body. Gmail messages have a nested mime structure; we want
# the text/html part. It may be at payload.body, payload.parts[i].body, or
# inside nested multipart.
function Get-HtmlBody {
    param($part)
    if ($part.mimeType -eq 'text/html' -and $part.body.data) {
        return $part.body.data
    }
    if ($part.parts) {
        foreach ($p in $part.parts) {
            $r = Get-HtmlBody $p
            if ($r) { return $r }
        }
    }
    return $null
}

$encodedHtml = Get-HtmlBody $pickedMessage.payload
if (-not $encodedHtml) {
    Log "No HTML body found in message." 'ERROR'
    exit 1
}

# Gmail returns base64url; convert to standard base64 then decode.
$standardB64 = $encodedHtml.Replace('-', '+').Replace('_', '/')
switch ($standardB64.Length % 4) {
    2 { $standardB64 += '==' }
    3 { $standardB64 += '=' }
}
$htmlBytes = [Convert]::FromBase64String($standardB64)
$rawHtml   = [System.Text.Encoding]::UTF8.GetString($htmlBytes)

Log "Extracted HTML body: $($rawHtml.Length) chars."

# 5. Wrap with the same styling we use on the in-browser scrape
$prettyDate = (Get-Date).ToUniversalTime().AddHours(5.5).ToString('dd MMM yyyy')
$wrappedHtml = @"
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>NutrioBox Daily Offer Tracker - $prettyDate</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1100px;margin:0 auto;padding:24px;color:#0f172a}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid #cbd5e1;padding:6px 10px}
th{background:#f1f5f9}
h1,h2,h3{color:#0f172a}
</style>
</head><body>
$rawHtml
</body></html>
"@

# 6. Upload to Supabase Storage
$objectName = "discount-codes-$todayIst.html"
$uploadUrl  = "$supabaseUrl/storage/v1/object/reports/$objectName"

Log "Uploading to $uploadUrl ..."

# Write body to a temp file and use curl (Invoke-WebRequest mangles binary)
$tmpFile = Join-Path $env:TEMP "nutriobox-discount-$todayIst.html"
[System.IO.File]::WriteAllText($tmpFile, $wrappedHtml, [System.Text.UTF8Encoding]::new($false))

$curlOutput = & curl.exe -sS -X PUT $uploadUrl `
    -H "Authorization: Bearer $secretKey" `
    -H "apikey: $secretKey" `
    -H "Content-Type: text/html; charset=utf-8" `
    -H "x-upsert: true" `
    -H "Cache-Control: public, max-age=60" `
    --data-binary "@$tmpFile" `
    -w "HTTP_STATUS=%{http_code}" 2>&1

Log "curl: $curlOutput"

if ($curlOutput -match 'HTTP_STATUS=200') {
    Log "Uploaded $objectName successfully."
    Log "Public URL: $supabaseUrl/storage/v1/object/public/reports/$objectName"
    Log "---- fetch-discount-email finished ----"
} else {
    Log "Upload failed." 'ERROR'
    exit 1
}

Remove-Item $tmpFile -ErrorAction SilentlyContinue
