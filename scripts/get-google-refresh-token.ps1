# One-time OAuth setup for the automated health check.
#
# Supersedes get-gmail-refresh-token.ps1, which only requested gmail.readonly.
# health-check.mjs additionally needs to READ the KOT Google Sheets and SEND
# the morning report, so this requests three scopes:
#
#   https://www.googleapis.com/auth/gmail.readonly        (Offer Tracker email)
#   https://www.googleapis.com/auth/gmail.send            (health report email)
#   https://www.googleapis.com/auth/spreadsheets.readonly (KOT tab names + gids)
#
# IMPORTANT: before running this, make sure the Google Sheets API is enabled
# for the project in Google Cloud Console -> APIs & Services -> Library.
# Also confirm the Google account you sign in with (mayank@nutriobox.com) has
# at least view access to both KOT spreadsheets.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\get-google-refresh-token.ps1

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile     = Join-Path $ProjectRoot '.env.local'
$RedirectUri = 'http://localhost:9123/'
$Scope       = 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/spreadsheets.readonly'

if (-not (Test-Path $EnvFile)) {
    Write-Host "Missing .env.local at $EnvFile" -ForegroundColor Red
    exit 1
}

$envVars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.+?)\s*$') { $envVars[$matches[1]] = $matches[2] }
}

$clientId     = $envVars['GMAIL_CLIENT_ID']
$clientSecret = $envVars['GMAIL_CLIENT_SECRET']

if (-not $clientId -or -not $clientSecret) {
    Write-Host "Missing GMAIL_CLIENT_ID or GMAIL_CLIENT_SECRET in .env.local" -ForegroundColor Red
    exit 1
}

$authUrl = 'https://accounts.google.com/o/oauth2/v2/auth?' + (
    @(
        "client_id=$([uri]::EscapeDataString($clientId))",
        "redirect_uri=$([uri]::EscapeDataString($RedirectUri))",
        'response_type=code',
        "scope=$([uri]::EscapeDataString($Scope))",
        'access_type=offline',
        'prompt=consent'
    ) -join '&'
)

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($RedirectUri)
$listener.Start()

Write-Host ""
Write-Host "Opening browser. Sign in as mayank@nutriobox.com and approve ALL THREE permissions."
Write-Host "If the browser doesn't open, paste this URL manually:"
Write-Host $authUrl -ForegroundColor Cyan
Write-Host ""
Start-Process $authUrl

Write-Host "Waiting for Google to redirect back to localhost:9123..."

$ctx  = $listener.GetContext()
$code = $ctx.Request.QueryString['code']
$err  = $ctx.Request.QueryString['error']

$resp = $ctx.Response
$html = if ($code) {
    '<html><body style="font-family:system-ui;text-align:center;padding:80px"><h1>Done!</h1><p>You can close this tab and return to PowerShell.</p></body></html>'
} else {
    "<html><body style='font-family:system-ui;text-align:center;padding:80px'><h1>Error</h1><p>$err</p></body></html>"
}
$bytes = [System.Text.Encoding]::UTF8.GetBytes($html)
$resp.ContentType = 'text/html; charset=utf-8'
$resp.ContentLength64 = $bytes.Length
$resp.OutputStream.Write($bytes, 0, $bytes.Length)
$resp.Close()
$listener.Stop()

if (-not $code) {
    Write-Host "OAuth failed: $err" -ForegroundColor Red
    exit 1
}

Write-Host "Got authorization code. Exchanging for refresh token..."

$tokenBody = @{
    code          = $code
    client_id     = $clientId
    client_secret = $clientSecret
    redirect_uri  = $RedirectUri
    grant_type    = 'authorization_code'
}

try {
    $tokenResp = Invoke-RestMethod -Method Post `
        -Uri 'https://oauth2.googleapis.com/token' `
        -Body $tokenBody `
        -ContentType 'application/x-www-form-urlencoded'
} catch {
    Write-Host "Token exchange failed: $_" -ForegroundColor Red
    exit 1
}

$refreshToken = $tokenResp.refresh_token
if (-not $refreshToken) {
    Write-Host "Google didn't return a refresh token - this client is already authorized." -ForegroundColor Red
    Write-Host "Go to https://myaccount.google.com/permissions, revoke the NutrioBox app, then re-run." -ForegroundColor Yellow
    exit 1
}

Write-Host "Granted scopes: $($tokenResp.scope)"

$lines = Get-Content $EnvFile
$updated = $false
$newLines = $lines | ForEach-Object {
    if ($_ -match '^GMAIL_REFRESH_TOKEN\s*=') { $updated = $true; "GMAIL_REFRESH_TOKEN=$refreshToken" }
    else { $_ }
}
if (-not $updated) { $newLines += "GMAIL_REFRESH_TOKEN=$refreshToken" }
Set-Content -Path $EnvFile -Value $newLines -NoNewline:$false

Write-Host ""
Write-Host "----------------------------------------------------" -ForegroundColor Green
Write-Host " Refresh token saved to .env.local.                  " -ForegroundColor Green
Write-Host "----------------------------------------------------" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: the old GMAIL_REFRESH_TOKEN has been replaced. If you also use it"
Write-Host "in GitHub Actions secrets, update it there too."
Write-Host ""
Write-Host "Test with:"
Write-Host "  node scripts\health-check.mjs --dry-run"
