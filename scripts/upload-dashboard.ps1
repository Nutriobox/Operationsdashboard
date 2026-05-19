# Uploads the newest NutrioBox dashboard HTML to Supabase Storage.
# - Reads the service_role key from .env.local (never committed to git).
# - Finds the newest NutrioBox_Dashboard_*.html in Downloads\NutrioBox_Reports\.
# - PUTs it into the "reports" bucket as sales-dashboard.html (upsert).
# - Logs to %USERPROFILE%\Desktop\nutriobox-deploy.log.

$ErrorActionPreference = 'Continue'

$ProjectRoot  = 'C:\Users\mayank\Documents\GitHub\Operationsdashboard'
$EnvFile      = Join-Path $ProjectRoot '.env.local'
$ReportsDir   = 'C:\Users\mayank\Downloads\NutrioBox_Reports'
$ReportGlob   = 'NutrioBox_Dashboard_*.html'
$BucketName   = 'reports'
$ObjectKey    = 'sales-dashboard.html'
$LogFile      = Join-Path $env:USERPROFILE 'Desktop\nutriobox-deploy.log'

function Log {
    param([string]$msg, [string]$level = 'INFO')
    $line = "[{0}] [{1}] [upload] {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $level, $msg
    $line | Tee-Object -FilePath $LogFile -Append | Out-Null
    Write-Host $line
}

Log "---- upload-dashboard starting ----"

# 1. Read SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from .env.local
if (-not (Test-Path $EnvFile)) {
    Log "Missing $EnvFile" 'ERROR'
    exit 1
}

$envVars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.+)\s*$') {
        $envVars[$matches[1]] = $matches[2]
    }
}

$supabaseUrl = $envVars['NEXT_PUBLIC_SUPABASE_URL']
$secretKey   = $envVars['SUPABASE_SERVICE_ROLE_KEY']

if (-not $supabaseUrl) { Log "NEXT_PUBLIC_SUPABASE_URL missing in .env.local" 'ERROR'; exit 1 }
if (-not $secretKey)   { Log "SUPABASE_SERVICE_ROLE_KEY missing in .env.local" 'ERROR'; exit 1 }

# 2. Find the newest dashboard HTML in Downloads
if (-not (Test-Path $ReportsDir)) {
    Log "Reports folder not found: $ReportsDir. Nothing to upload."
    exit 0
}

$latest = Get-ChildItem -Path $ReportsDir -Filter $ReportGlob -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($null -eq $latest) {
    Log "No NutrioBox_Dashboard_*.html in $ReportsDir. Nothing to upload."
    exit 0
}

$sizeMb = [math]::Round($latest.Length / 1MB, 2)
Log ("Latest report: {0} ({1} MB, modified {2})" -f $latest.Name, $sizeMb, $latest.LastWriteTime)

# 3. Skip if Supabase already has the same byte count
$publicUrl  = "$supabaseUrl/storage/v1/object/public/$BucketName/$ObjectKey"
$uploadUrl  = "$supabaseUrl/storage/v1/object/$BucketName/$ObjectKey"

try {
    $head = Invoke-WebRequest -Uri $publicUrl -Method Head -UseBasicParsing -ErrorAction SilentlyContinue
    if ($head -and $head.Headers['Content-Length']) {
        $remoteSize = [int64]$head.Headers['Content-Length']
        if ($remoteSize -eq $latest.Length) {
            Log "Supabase copy is already the same size ($remoteSize bytes). Skipping upload."
            Log "---- upload-dashboard finished (no-op) ----"
            exit 0
        }
    }
} catch {
    # 404 or other — proceed to upload
}

# 4. Upload via curl.exe (PowerShell's Invoke-* struggles with large binary uploads).
Log ("Uploading to {0}" -f $uploadUrl)
$curlArgs = @(
    '-X','POST',
    $uploadUrl,
    '-H', ("apikey: {0}" -f $secretKey),
    '-H', ("Authorization: Bearer {0}" -f $secretKey),
    '-H', 'Content-Type: text/html',
    '-H', 'x-upsert: true',
    '--data-binary', ("@{0}" -f $latest.FullName),
    '--silent', '--show-error',
    '--write-out', 'HTTP_STATUS=%{http_code}'
)

$curlOutput = & curl.exe @curlArgs 2>&1
$curlOutput | ForEach-Object { Log ("  > {0}" -f $_) }

if ($curlOutput -match 'HTTP_STATUS=(\d+)') {
    $status = [int]$matches[1]
    if ($status -ge 200 -and $status -lt 300) {
        Log ("Upload succeeded ({0}). Public URL: {1}" -f $status, $publicUrl)
        Log "---- upload-dashboard finished ----"
        exit 0
    } else {
        Log ("Upload failed with HTTP {0}" -f $status) 'ERROR'
        Log "Check that the 'reports' bucket exists and the file size limit is high enough." 'ERROR'
        exit 1
    }
}

Log "curl returned no status code. Check curl output above." 'ERROR'
exit 1
