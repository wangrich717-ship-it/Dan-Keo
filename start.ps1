# Dan Koe Knowledge Base - Launcher
# Run this in PowerShell to build data and start local server

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host ""
Write-Host "  Dan Koe Knowledge Base" -ForegroundColor Yellow
Write-Host "  ─────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Step 1: Build data if needed
$IndexFile = Join-Path $ScriptDir "data\index.json"
if (-not (Test-Path $IndexFile)) {
    Write-Host "  [1/2] Building data from articles..." -ForegroundColor Cyan
    python build_data.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Python build failed. Make sure Python 3 is installed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "  [1/2] Data already built. Skipping... (delete data\ to rebuild)" -ForegroundColor DarkGray
}

# Step 2: Start HTTP server
Write-Host "  [2/2] Starting local server at http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Ctrl+C to stop the server." -ForegroundColor DarkGray
Write-Host ""

# Open browser
Start-Process "http://localhost:8080"

# Start Python HTTP server
python -m http.server 8080
