# Auto-deploy script for Nutriobox Operations Dashboard.
# Deploys CODE changes only. The big dashboard HTML file goes to Supabase
# Storage via a separate script (Upload-Dashboard.ps1) because it's too
# large for GitHub (>100 MB per-file limit).
#
# Run manually (double-click Deploy.bat on desktop) or on schedule
# (daily 9am Windows scheduled task created by Setup-Daily-Schedule.bat).

$ErrorActionPreference = 'Continue'

$ProjectRoot = 'C:\Users\hp\Downloads\Operationsdashboard'
$LogFile     = Join-Path $env:USERPROFILE 'Desktop\nutriobox-deploy.log'
$MaxBlobBytes = 90MB   # safety margin below GitHub's 100MB cap

function Log {
    param([string]$msg, [string]$level = 'INFO')
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $level, $msg
    $line | Tee-Object -FilePath $LogFile -Append | Out-Null
    Write-Host $line
}

function Run-Git {
    param([string[]]$ArgList)
    if (Test-Path "$ProjectRoot\.git\index.lock") {
        Remove-Item "$ProjectRoot\.git\index.lock" -Force -ErrorAction SilentlyContinue
    }
    Log ("git " + ($ArgList -join ' '))
    $output = & git -C $ProjectRoot @ArgList 2>&1
    $output | ForEach-Object { Log ("  > {0}" -f $_) }
    return $LASTEXITCODE
}

Log "================ Auto-deploy run starting ================"

if (-not (Test-Path $ProjectRoot)) {
    Log "Project root not found: $ProjectRoot" 'ERROR'
    exit 1
}

# Make sure commits are authored with an email that's verified on GitHub.
# Vercel blocks deploys when the commit email doesn't match the GitHub account.
& git -C $ProjectRoot config user.email "mayank@nutriobox.com" 2>$null
& git -C $ProjectRoot config user.name "Nutriobox" 2>$null

# Step 0: upload the latest dashboard HTML to Supabase Storage.
# Done first because if the dashboard hasn't changed there's nothing to push.
$uploadScript = Join-Path $ProjectRoot 'scripts\upload-dashboard.ps1'
if (Test-Path $uploadScript) {
    Log "Running upload-dashboard.ps1..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $uploadScript | Out-Null
    Log "Upload step finished (exit $LASTEXITCODE)."
} else {
    Log "upload-dashboard.ps1 not found; skipping Supabase upload." 'WARN'
}

# Defensive: clear any corrupt index that might be lingering.
$statusProbe = & git -C $ProjectRoot status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) {
    Log "Git index looks broken; resetting." 'WARN'
    if (Test-Path "$ProjectRoot\.git\index") {
        Remove-Item "$ProjectRoot\.git\index" -Force
    }
    & git -C $ProjectRoot reset HEAD 2>&1 | Out-Null
    $statusProbe = & git -C $ProjectRoot status --porcelain 2>&1
}

# Sync with remote first so we don't try to push behind history.
Log "Fetching origin..."
Run-Git @('fetch','origin') | Out-Null

# Look for any pending changes.
if (-not $statusProbe) {
    Log "Working tree clean. Nothing to commit."
    Log "================ Auto-deploy run finished ================"
    Log ""
    exit 0
}

Log "Pending changes:"
$statusProbe | ForEach-Object { Log ("  > {0}" -f $_) }

# Safety check: refuse to stage any file >90MB.
$oversized = @()
$statusProbe | ForEach-Object {
    # porcelain lines look like " M path" or "?? path"
    $path = ($_ -replace '^.{2,3}\s+','').Trim('"')
    $full = Join-Path $ProjectRoot $path
    if (Test-Path $full -PathType Leaf) {
        $size = (Get-Item $full).Length
        if ($size -gt $MaxBlobBytes) {
            $oversized += [pscustomobject]@{ Path = $path; Size = $size }
        }
    }
}

if ($oversized.Count -gt 0) {
    Log "Refusing to stage these oversized files (>90MB):" 'WARN'
    $oversized | ForEach-Object {
        Log ("  > {0} ({1:N1} MB)" -f $_.Path, ($_.Size / 1MB)) 'WARN'
    }
    Log "These files need Supabase Storage or Git LFS, not regular git." 'WARN'
    Log "Continuing with remaining files only."
}

# Stage everything except oversized files.
Run-Git @('add','-A') | Out-Null
foreach ($f in $oversized) {
    Run-Git @('reset','HEAD','--', $f.Path) | Out-Null
}

# Did anything end up staged?
$staged = & git -C $ProjectRoot diff --cached --name-only 2>$null
if (-not $staged) {
    Log "Nothing safe to commit. Done."
    Log "================ Auto-deploy run finished ================"
    Log ""
    exit 0
}

$commitMsg = "Auto-deploy: {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm')
if ((Run-Git @('commit','-m',$commitMsg)) -ne 0) {
    Log "git commit failed." 'WARN'
}

if ((Run-Git @('push','origin','main')) -ne 0) {
    Log "git push failed. Try Reset-Git-State.bat then re-run Deploy.bat." 'ERROR'
    exit 1
}

Log "Push succeeded. Railway will redeploy in about 60 seconds."
Log "================ Auto-deploy run finished ================"
Log ""
exit 0
