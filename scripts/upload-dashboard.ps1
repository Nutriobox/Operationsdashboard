# Uploads the newest NutrioBox dashboard HTML to Supabase Storage.
# - Reads the service_role key from .env.local (never committed to git).
# - Finds the newest NutrioBox_Dashboard_*.html in Downloads\NutrioBox_Reports\.
# - PUTs it into the "reports" bucket as sales-dashboard.html (upsert).
# - Logs to %USERPROFILE%\Desktop\nutriobox-deploy.log.

$ErrorActionPreference = 'Continue'

$ProjectRoot  = 'C:\Users\hp\Downloads\Operationsdashboard'
$EnvFile      = Join-Path $ProjectRoot '.env.local'
$ReportsDir   = 'C:\Users\hp\Downloads\NutrioBox_Reports'
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

# Find the newest FULL export (exclude the shrunk SERVED copy we write below).
$latest = Get-ChildItem -Path $ReportsDir -Filter $ReportGlob -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notlike '*SERVED*' } |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($null -eq $latest) {
    Log "No NutrioBox_Dashboard_*.html in $ReportsDir. Nothing to upload."
    exit 0
}

$sizeMb = [math]::Round($latest.Length / 1MB, 2)
Log ("Latest full report: {0} ({1} MB, modified {2})" -f $latest.Name, $sizeMb, $latest.LastWriteTime)

# --- 2026-10-21: SHRINK before upload ------------------------------------
# The raw export embeds a full year of order-line DAILY_DATA (~172 MB / ~12 MB
# gzip). That exceeds the Vercel proxy's ~4.5 MB response cap, so /api/sales-
# dashboard returned an empty body and the dashboard hung on "rendering".
# shrink_dashboard.py keeps full intraday detail for the last 50 days and lets
# older dates fall back to the monthly view, landing ~4 MB gzip (well under the
# cap) and rendering ~4x lighter. We write the shrunk copy as *_SERVED.html so
# EVERY uploader (this script AND the daily health-check's hash-compare, which
# both pick the newest NutrioBox_Dashboard_*.html) treats the shrunk file as
# canonical and stays consistent. If the shrink fails we DO NOT fall back to the
# 172 MB file (that would re-break serving) — we abort and let the next run /
# the health-check retry.
$Shrinker = 'C:\Users\hp\Downloads\Operationsdashboard\automation\shrink_dashboard.py'
$served   = Join-Path $ReportsDir 'NutrioBox_Dashboard_SERVED.html'
Log "Shrinking $($latest.Name) -> NutrioBox_Dashboard_SERVED.html (50-day window)..."
& python $Shrinker $latest.FullName $served --days 50 --older drop 2>&1 | ForEach-Object { Log ("  shrink> {0}" -f $_) }
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $served)) {
    Log "Shrink failed (exit $LASTEXITCODE). NOT uploading the full file — aborting to avoid re-breaking the proxy." 'ERROR'
    exit 1
}
# Upload the shrunk copy from here on.
$latest = Get-Item $served
$sizeMb = [math]::Round($latest.Length / 1MB, 2)
Log ("Shrunk report ready: {0} ({1} MB)" -f $latest.Name, $sizeMb)
# -------------------------------------------------------------------------

# 3. Supabase Free plan caps files at 50 MB. The raw HTML is often well over
#    that, but it gzip-compresses dramatically (Plotly/embedded data is mostly
#    text). Compress to a temp file first.
$gzPath = Join-Path $env:TEMP 'nutriobox-sales-dashboard.html.gz'
if (Test-Path $gzPath) { Remove-Item $gzPath -Force }

Log "Gzipping..."
$inStream  = [System.IO.File]::OpenRead($latest.FullName)
$outStream = [System.IO.File]::Create($gzPath)
$gzStream  = New-Object System.IO.Compression.GZipStream($outStream, [System.IO.Compression.CompressionLevel]::Optimal)
$inStream.CopyTo($gzStream)
$gzStream.Close(); $outStream.Close(); $inStream.Close()

$gzFile = Get-Item $gzPath
$gzMb = [math]::Round($gzFile.Length / 1MB, 2)
Log ("Compressed: {0} MB (from {1} MB, ratio {2}%)" -f $gzMb, $sizeMb, [math]::Round(100 * $gzFile.Length / $latest.Length, 1))

if ($gzFile.Length -gt 50MB) {
    Log "Compressed file still over 50 MB. Supabase Free plan cannot accept it." 'ERROR'
    Log "Options: (1) upgrade Supabase Pro, (2) host on Cloudflare R2, (3) trim the dashboard." 'ERROR'
    exit 1
}

# 4. Skip if Supabase already has the same byte count for the compressed file.
$publicUrl  = "$supabaseUrl/storage/v1/object/public/$BucketName/$ObjectKey"
$uploadUrl  = "$supabaseUrl/storage/v1/object/$BucketName/$ObjectKey"

try {
    $head = Invoke-WebRequest -Uri $publicUrl -Method Head -UseBasicParsing -ErrorAction SilentlyContinue
    if ($head -and $head.Headers['Content-Length']) {
        $remoteSize = [int64]$head.Headers['Content-Length']
        if ($remoteSize -eq $gzFile.Length) {
            Log "Supabase copy already matches compressed size ($remoteSize bytes). Skipping upload."
            Log "---- upload-dashboard finished (no-op) ----"
            exit 0
        }
    }
} catch {
    # 404 or other - proceed to upload
}

# 5. Upload via curl.exe. Set Content-Encoding: gzip so browsers transparently
#    decompress; the iframe URL still loads as HTML.
Log ("Uploading to {0}" -f $uploadUrl)
$curlArgs = @(
    '-X','POST',
    $uploadUrl,
    '-H', ("apikey: {0}" -f $secretKey),
    '-H', ("Authorization: Bearer {0}" -f $secretKey),
    '-H', 'Content-Type: text/html',
    '-H', 'Content-Encoding: gzip',
    '-H', 'Cache-Control: no-cache',
    '-H', 'x-upsert: true',
    '--data-binary', ("@{0}" -f $gzFile.FullName),
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
