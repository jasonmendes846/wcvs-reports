# WCVS Local Preview Server
# Starts a Python HTTP server to preview the website locally

$ProjectRoot = "C:\Users\jimmy\Projects\wcvs-platform"
$WebsiteDir = "$ProjectRoot\outputs\website"
$Port = 8000

if (-not (Test-Path $WebsiteDir)) {
    Write-Error "Website not found at $WebsiteDir. Run 'python -m src.website.builder' first."
    exit 1
}

Write-Host "Starting WCVS preview server..."
Write-Host "  Directory: $WebsiteDir"
Write-Host "  URL:       http://localhost:$Port"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host ""

# Start server in background job
$job = Start-Job -ScriptBlock {
    param($dir, $port)
    Set-Location $dir
    python -m http.server $port
} -ArgumentList $WebsiteDir, $Port

# Wait a moment for server to start
Start-Sleep -Seconds 2

# Open browser
Start-Process "http://localhost:$Port"

# Keep script alive until user presses key
Write-Host "Server running. Press Enter to stop..."
[void][System.Console]::ReadLine()

Stop-Job $job
Remove-Job $job
Write-Host "Server stopped."
