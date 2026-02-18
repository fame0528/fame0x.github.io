# Income Bot Rollback Script
# Rolls back the live_site repository to a previous commit

param(
    [Parameter(Mandatory=$true)]
    [string]$CommitSha
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
$repoPath = Join-Path $scriptDir "live_site"

if (-not (Test-Path $repoPath)) {
    Write-Host "❌ Repository not found at $repoPath" -ForegroundColor Red
    exit 1
}

Write-Host "Rolling back live_site to commit $CommitSha" -ForegroundColor Yellow
Write-Host "Repository: $repoPath" -ForegroundColor Gray

Set-Location $repoPath

# Verify commit exists
$exists = git cat-file -e "$CommitSha^{commit}" 2>$null
if (-not $exists) {
    Write-Host "❌ Commit $CommitSha does not exist in this repository." -ForegroundColor Red
    Write-Host "Use 'git log --oneline' to see available commits." -ForegroundColor Yellow
    exit 1
}

# Show what will be reverted
Write-Host "`nCommits to be reverted:" -ForegroundColor Cyan
git log --oneline $CommitSha..HEAD

$confirm = Read-Host "`nThis will revert these commits. Continue? (y/N)"
if ($confirm -notmatch '^[Yy]') {
    Write-Host "Rollback cancelled." -ForegroundColor Yellow
    exit 0
}

# Perform revert
try {
    git revert --no-commit $CommitSha..HEAD | Out-Null
    $msg = "Rollback to $CommitSha - emergency hotfix"
    git commit -m $msg
    git push origin main
    Write-Host "✅ Rollback successful. Pushed revert commit." -ForegroundColor Green

    # Also roll back Income Bot code if we're in test mode? Not needed for live site.
} catch {
    Write-Host "❌ Rollback failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Post-Rollback Steps ===" -ForegroundColor Cyan
Write-Host "1. Verify site still works: https://YOURUSERNAME.github.io"
Write-Host "2. Check Actions tab for any failing workflows"
Write-Host "3. Investigate what caused the bad state before re-enabling automation"