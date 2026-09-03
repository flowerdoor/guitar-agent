$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

python -m PyInstaller --noconfirm --clean GuitarCoach.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Copy-Item -LiteralPath "config.example.json" -Destination "dist\GuitarCoach\config.example.json" -Force
Copy-Item -LiteralPath "config.example.json" -Destination "dist\GuitarCoach\config.local.json" -Force

Write-Host "Build complete: dist\GuitarCoach\GuitarCoach.exe"
