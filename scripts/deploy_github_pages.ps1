# WCVS GitHub Pages Deployment Script
# Usage:
#   .\scripts\deploy_github_pages.ps1 -Repo "USERNAME/wcvs-reports" [-BasePath "/wcvs-reports"]
#
# Prerequisites:
#   1. Git installed and configured with your GitHub credentials
#   2. GitHub repo created (e.g., https://github.com/USERNAME/wcvs-reports)
#   3. GitHub Pages enabled in repo settings (Source: docs folder)

param(
    [Parameter(Mandatory=$true)]
    [string]$Repo,

    [string]$BasePath = "",

    [string]$Branch = "main",

    [switch]$SkipBuild
)

$ProjectRoot = "C:\Users\jimmy\Projects\wcvs-platform"
$DocsDir = "$ProjectRoot\docs"

# Ensure we're in the project directory
Set-Location $ProjectRoot

# Step 1: Build website with correct base path
if (-not $SkipBuild) {
    Write-Host "[DEPLOY] Building website with base path: '$BasePath'..."
    python -m src.website.builder --base-path "$BasePath"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Website build failed. Aborting deployment."
        exit 1
    }
}

# Step 2: Copy website to docs/ folder
Write-Host "[DEPLOY] Copying website to docs/ folder..."
if (Test-Path $DocsDir) {
    Remove-Item -Recurse -Force $DocsDir
}
Copy-Item -Recurse -Path "$ProjectRoot\outputs\website" -Destination $DocsDir

# Step 3: Add .nojekyll to prevent GitHub Pages from ignoring files starting with underscore
New-Item -ItemType File -Path "$DocsDir\.nojekyll" -Force | Out-Null

# Step 4: Git commit and push
Write-Host "[DEPLOY] Committing and pushing to GitHub..."
git add docs/
git add src/
git add scripts/
git add requirements.txt
git add README.md
git add .gitignore

$CommitMessage = "Deploy WCVS website - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git commit -m "$CommitMessage" --allow-empty

# Check if remote exists
$remotes = git remote
if ($remotes -notcontains "origin") {
    Write-Host "[DEPLOY] Adding GitHub remote: https://github.com/$Repo.git"
    git remote add origin "https://github.com/$Repo.git"
}

# Push
git push -u origin $Branch

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "  DEPLOYMENT SUCCESSFUL"
    Write-Host "=========================================="
    Write-Host ""
    Write-Host "  Repository:  https://github.com/$Repo"
    if ($BasePath -eq "") {
        Write-Host "  Website URL: https://$(($Repo -split '/')[0]).github.io/$(($Repo -split '/')[1])/"
    } else {
        Write-Host "  Website URL: https://$(($Repo -split '/')[0]).github.io$(($BasePath -replace '/$',''))/"
    }
    Write-Host ""
    Write-Host "  Next steps:"
    Write-Host "    1. Go to https://github.com/$Repo/settings/pages"
    Write-Host "    2. Set Source to 'Deploy from a branch'"
    Write-Host "    3. Select branch '$Branch' and folder '/docs'"
    Write-Host "    4. Click Save"
    Write-Host "    5. Wait 1-2 minutes for site to go live"
    Write-Host "=========================================="
} else {
    Write-Error "Git push failed. Check your credentials and remote URL."
    exit 1
}
