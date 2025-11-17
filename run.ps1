# yt-player-launcher.ps1
# PowerShell launcher for yt_audio_player.py

$target = "C:\Users\devan\Desktop\yt-dlp cmd player"

if (-Not (Test-Path $target)) {
    Write-Error "Directory not found: $target"
    exit 1
}

Push-Location $target

# choose audio or video
Write-Host ""
Write-Host "Choose mode:"
Write-Host "  1) Audio only"
Write-Host "  2) Video"
$top = Read-Host "Enter 1 or 2"
switch ($top) {
    "1" { $videoFlag = "" ; Write-Host "Selected: Audio only" }
    "2" { $videoFlag = "--video" ; Write-Host "Selected: Video" }
    default {
        Write-Warning "Invalid choice. Defaulting to Audio only."
        $videoFlag = ""
    }
}

# choose play mode
Write-Host ""
Write-Host "Choose play mode:"
Write-Host "  1) interactive play"
Write-Host "  2) offline"
Write-Host "  3) playlist (shuffle all)"
$mode = Read-Host "Enter 1, 2, or 3"

# build command
$scriptName = "yt_audio_player.py"
$args = @()

switch ($mode) {
    "1" { }                          # interactive -> no extra flags
    "2" { $args += "--offline" }
    "3" { $args += "--list"; $args += "--shuffle-all" }
    default { Write-Warning "Invalid choice. Defaulting to interactive."; }
}

if ($videoFlag) { $args += $videoFlag }

# prepare and show
$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { Write-Error "python not found in PATH"; Pop-Location; exit 1 }

Write-Host ""
Write-Host "Ready to run:"
Write-Host "  $pythonCmd $scriptName $($args -join ' ')"
Write-Host ""

# run
& $pythonCmd $scriptName @args
$rc = $LASTEXITCODE

Pop-Location
exit $rc
