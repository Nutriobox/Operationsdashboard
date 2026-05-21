# One-time OAuth setup for Gmail API access.
#
# Run this ONCE after you've created the OAuth Desktop credentials in Google
# Cloud Console. It:
#   1. Reads GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET from .env.local.
#   2. Spins up a local HTTP server on http://localhost:9123/.
#   3. Opens your browser to Google's OAuth consent page.
#   4. You sign in once and approve gmail.readonly scope.
#   5. Google redirects back to localhost:9123 with an auth code.
#   6. Script exchanges the code for a long-lived refresh token.
#   7. Saves the refresh token to .env.local.
#
# After this runs, fetch-discount-email.ps1 can read your inbox forever
# without further interaction. The refresh token never expires until you
# manually revoke it from https://myaccount.google.com/permissions.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\get-gmail-refresh-token.ps1

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile     = Join-Path $ProjectRoot '.env.local'
$RedirectUri = 'http://localhost:9123/'
$Scope       = 'https://www.googleapis.com/auth/gmail.readonly'

if (-not (Test-Path $EnvFile)) {
    Write-Host "Missing .env.local at $EnvFile" -ForegroundColor Red
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

if (-not $clientId -or -not $clientSecret) {
    Write-Host "Missing GMAIL_CLIENT_ID or GMAIL_CLIENT_SECRET in .env.local" -ForegroundColor Red
    Write-Host "Add them like:"
    Write-Host '  GMAIL_CLIENT_ID=xxx.apps.googleusercontent.com'
    Write-Host '  GMAIL_CLIENT_SECRET=GOCSPX-xxx'
    exit 1
}

Write-Host "Starting local callback server on $RedirectUri ..."

# Build the auth URL
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

# Start the listener
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($RedirectUri)
$listener.Start()

Write-Host ""
Write-Host "Opening browser..."
Write-Host "If it doesn't open, paste this URL manually:"
Write-Host $authUrl -ForegroundColor Cyan
Write-Host ""
Start-Process $authUrl

Write-Host "Waiting for Google to redirect back to localhost:9123..."

$ctx = $listener.GetContext()
$code = $ctx.Request.QueryString['code']
$err  = $ctx.Request.QueryString['error']

# Send a friendly page back to the browser
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
    Write-Host "Google didn't return a refresh token. This usually means you've already authorized this client." -ForegroundColor Red
    Write-Host "Go to https://myaccount.google.com/permissions, revoke 'NutrioBox Email Sync', then re-run this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "Got refresh token. Saving to .env.local..."

$lines = Get-Content $EnvFile
$updated = $false
$newLines = $lines | ForEach-Object {
    if ($_ -match '^GMAIL_REFRESH_TOKEN\s*=') {
        $updated = $true
        "GMAIL_REFRESH_TOKEN=$refreshToken"
    } else {
        $_
    }
}
if (-not $updated) {
    $newLines += "GMAIL_REFRESH_TOKEN=$refreshToken"
}
Set-Content -Path $EnvFile -Value $newLines -NoNewline:$false

Write-Host ""
Write-Host "----------------------------------------------------" -ForegroundColor Green
Write-Host " Setup complete. Refresh token saved to .env.local. " -ForegroundColor Green
Write-Host "----------------------------------------------------" -ForegroundColor Green
Write-Host ""
Write-Host "Test it by running:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\fetch-discount-email.ps1"
