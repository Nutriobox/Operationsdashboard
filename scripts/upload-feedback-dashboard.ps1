# Uploads the Customer Feedback dashboard HTML to Supabase Storage.
# - Reads the service_role key from .env.local (never committed to git).
# - Uploads C:\Users\mayank\Downloads\NutrioBox_Feedback_Dashboard.html
#   into the "reports" bucket as feedback-dashboard.html (upsert).
# - The site's /api/feedback-dashboard route re-serves this file into the
#   Customer Feedback tab, so a refresh of the site shows the new version.
# - Logs to %USERPROFILE%\Desktop\nutriobox-deploy.log.

$ErrorActionPreference = 'Continue'

$ProjectRoot = 'C:\Users\mayank\Documents\GitHub\Operationsdashboard'
$EnvFile     = Join-Path $ProjectRoot '.env.local'
$SourceFile  = 'C:\Users\mayank\Downloads\NutrioBox_Feedback_Dashboard.html'
$BucketName  = 'reports'
$ObjectKey   = 'feedback-dashboard.html'
$LogFile     = Join-Path $env:USERPROFILE 'Desktop\nutriobox-deploy.log'

function Log {
    param([string]$msg, [string]$level = 'INFO')
    $line = "[{0}] [{1}] [feedback-upload] {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $level, $msg
    $line | Tee-Object -FilePath $LogFile -Append | Out-Null
    Write-Host $line
}

Log "---- upload-feedback-dashboard starting ----"

# 1. Read SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from .env.local
if (-not (Test-Path $EnvFile)) { Log "Missing $EnvFile" 'ERROR'; Read-Host 'Press Enter to close'; exit 1 }

$envVars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.+)\s*$') { $envVars[$matches[1]] = $matches[2] }
}
$supabaseUrl = $envVars['NEXT_PUBLIC_SUPABASE_URL']
$secretKey   = $envVars['SUPABASE_SERVICE_ROLE_KEY']

if (-not $supabaseUrl) { Log "NEXT_PUBLIC_SUPABASE_URL missing in .env.local" 'ERROR'; Read-Host 'Press Enter to close'; exit 1 }
if (-not $secretKey)   { Log "SUPABASE_SERVICE_ROLE_KEY missing in .env.local" 'ERROR'; Read-Host 'Press Enter to close'; exit 1 }

# 2. Confirm the source file exists
if (-not (Test-Path $SourceFile)) { Log "Source not found: $SourceFile" 'ERROR'; Read-Host 'Press Enter to close'; exit 1 }
$sizeKb = [math]::Round((Get-Item $SourceFile).Length / 1KB, 1)
Log ("Source: {0} ({1} KB)" -f $SourceFile, $sizeKb)

# 3. Upload via curl.exe (upsert overwrites the existing object).
$publicUrl = "$supabaseUrl/storage/v1/object/public/$BucketName/$ObjectKey"
$uploadUrl = "$supabaseUrl/storage/v1/object/$BucketName/$ObjectKey"
Log ("Uploading to {0}" -f $uploadUrl)

$curlArgs = @(
    '-X','POST', $uploadUrl,
    '-H', ("apikey: {0}" -f $secretKey),
    '-H', ("Authorization: Bearer {0}" -f $secretKey),
    '-H', 'Content-Type: text/html',
    '-H', 'Cache-Control: no-cache',
    '-H', 'x-upsert: true',
    '--data-binary', ("@{0}" -f $SourceFile),
    '--silent', '--show-error',
    '--write-out', 'HTTP_STATUS=%{http_code}'
)
$curlOutput = & curl.exe @curlArgs 2>&1
$curlOutput | ForEach-Object { Log ("  > {0}" -f $_) }

if ($curlOutput -match 'HTTP_STATUS=(\d+)') {
    $status = [int]$matches[1]
    if ($status -ge 200 -and $status -lt 300) {
        Log ("Upload succeeded ({0}). Public URL: {1}" -f $status, $publicUrl)
        Log "---- upload-feedback-dashboard finished ----"
        Write-Host ''
        Write-Host 'DONE. Refresh opsdashboard.nutriobox.com/dashboard/feedback (hard refresh: Ctrl+F5).'
        Read-Host 'Press Enter to close'
        exit 0
    } else {
        Log ("Upload failed with HTTP {0}" -f $status) 'ERROR'
        Log "Check that the 'reports' bucket exists and the service_role key is valid." 'ERROR'
        Read-Host 'Press Enter to close'
        exit 1
    }
}

Log "curl returned no status code. Check curl output above." 'ERROR'
Read-Host 'Press Enter to close'
exit 1
