# Income Bot Installer for Windows
# Sets up local Task Scheduler job to run daily at 8 AM (in addition to GitHub Actions)

$ErrorActionPreference = "Stop"

Write-Host "=== Income Bot Installer ===" -ForegroundColor Cyan

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found in PATH. Install Python 3.11+ first." -ForegroundColor Red
    exit 1
}
python --version

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git not found in PATH. Install Git first." -ForegroundColor Red
    exit 1
}
git --version

# Verify repo structure
$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
$repoPath = Join-Path $scriptDir "live_site"
if (-not (Test-Path $repoPath)) {
    Write-Host "❌ Repository not found at $repoPath" -ForegroundColor Red
    Write-Host "Please clone your GitHub Pages repo first:" -ForegroundColor Yellow
    Write-Host "  git clone https://github.com/YOURUSERNAME/YOURUSERNAME.github.io.git live_site" -ForegroundColor White
    exit 1
}

# Create data directory if not exists
$dataDir = Join-Path $scriptDir "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    Write-Host "✅ Created data directory" -ForegroundColor Green
}

# Set up daily task in Task Scheduler
$taskName = "Income Bot Daily Run"
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "`"$scriptDir\run.py`" --once"
$trigger = New-ScheduledTaskTrigger -Daily -At 8AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
$principal = New-ScheduledTaskPrincipal -UserId "CURRENTUSER"

# Check if task already exists
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Task '$taskName' already exists. Updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
Write-Host "✅ Scheduled task created: $taskName (runs daily at 8 AM)" -ForegroundColor Green

# Verify config exists
$configPath = Join-Path $scriptDir "config.yaml"
if (-not (Test-Path $configPath)) {
    Write-Host "⚠️  config.yaml not found. Copy from config.yaml.example and fill in your values." -ForegroundColor Yellow
}

# Final message
Write-Host "`n=== Installation Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Edit config.yaml with your Gemini API key and affiliate IDs"
Write-Host "2. Run: python run.py --setup"
Write-Host "3. Run: python run.py --once (test)"
Write-Host "4. Check: python run.py --health"
Write-Host "5. Enable GitHub Actions and add GEMINI_API_KEY secret"
Write-Host "" -ForegroundColor Green