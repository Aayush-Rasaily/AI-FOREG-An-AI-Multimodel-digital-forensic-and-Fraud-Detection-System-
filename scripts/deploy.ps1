# Production deploy (Windows): build, migrate via compose, start, probe.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$EnvFile = if ($env:ENV_FILE) { $env:ENV_FILE } else { ".env.production" }
if (-not (Test-Path $EnvFile)) {
  throw "Missing $EnvFile. Copy .env.production.example and set secrets."
}

try {
  $env:GIT_COMMIT = (git rev-parse HEAD)
} catch {
  $env:GIT_COMMIT = ""
}
$env:BUILD_ID = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")

$Compose = "docker compose -f docker-compose.prod.yml --env-file $EnvFile"
Write-Host "[deploy] Building production images..."
Invoke-Expression "$Compose build"
Write-Host "[deploy] Starting stack (migrations run first)..."
Invoke-Expression "$Compose up -d --remove-orphans"

$Port = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
Write-Host "[deploy] Waiting for API liveness..."
for ($i = 0; $i -lt 60; $i++) {
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/v1/system/liveness" -UseBasicParsing | Out-Null
    Write-Host "[deploy] Liveness OK."
    break
  } catch {
    Start-Sleep -Seconds 2
  }
}

Write-Host "[deploy] Complete."
