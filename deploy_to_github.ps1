# deploy_to_github.ps1
# Automates creating the GitHub repository, pushing code, and configuring secrets.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Daily Market Summary - GitHub Deployment Setup" -ForegroundColor Cyan
Write-Host "=========================================================="

# Check if gh CLI is authenticated
$authCheck = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[!] You are not yet logged in to GitHub." -ForegroundColor Yellow
    Write-Host "Please authenticate with GitHub by running:" -ForegroundColor White
    Write-Host "  gh auth login" -ForegroundColor Green
    Write-Host "`nFollow the prompts (choose GitHub.com -> HTTPS -> Login with a web browser)." -ForegroundColor Gray
    exit 1
}

Write-Host "`n[1/3] Creating GitHub repository and pushing code..." -ForegroundColor Cyan
# Ask or default to public (public has unlimited free Actions minutes)
gh repo create Daily_Market_Update --public --source=. --remote=origin --push

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nRepository may already exist or there was a push issue. Attempting git push origin main..." -ForegroundColor Yellow
    git push -u origin main
}

Write-Host "`n[2/3] Setting GOOGLE_AI_API_KEY secret in GitHub..." -ForegroundColor Cyan
$apiKey = ($env:GOOGLE_AI_API_KEY -replace '^\s+|\s+$', '')
if ($apiKey) {
    gh secret set GOOGLE_AI_API_KEY --body "$apiKey"
    Write-Host "[OK] GOOGLE_AI_API_KEY secret saved to repository." -ForegroundColor Green
} else {
    Write-Host "[!] GOOGLE_AI_API_KEY environment variable not found on local machine." -ForegroundColor Yellow
    Write-Host "Please set it manually in: Repo -> Settings -> Secrets and variables -> Actions" -ForegroundColor Gray
}

Write-Host "`n[3/3] Triggering initial test run on GitHub Actions..." -ForegroundColor Cyan
gh workflow run "daily_update.yml"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Setup Complete! Your cloud runner is active." -ForegroundColor Green
Write-Host "=========================================================="
Write-Host "`nNext Steps to enable GitHub Pages:"
Write-Host "1. Go to: https://github.com/$(gh api user -q .login)/Daily_Market_Update/settings/pages"
Write-Host "2. Under 'Build and deployment' -> 'Source', select: GitHub Actions"
Write-Host "`nYour site will be live and auto-updating at:" -ForegroundColor Cyan
Write-Host "https://$(gh api user -q .login).github.io/Daily_Market_Update/" -ForegroundColor Green
