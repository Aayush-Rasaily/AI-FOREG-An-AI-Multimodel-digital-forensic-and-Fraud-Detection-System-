# Static asset production build (Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "frontend")

Write-Host "[build-frontend] Installing dependencies..."
npm ci
Write-Host "[build-frontend] Building static assets..."
node ./scripts/build.mjs
Write-Host "[build-frontend] Output: frontend/dist"
