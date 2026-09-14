# Apply Alembic migrations (Windows). Prefer local .env for native development.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$EnvFile = if ($env:ENV_FILE) {
  $env:ENV_FILE
} elseif (Test-Path ".env") {
  ".env"
} elseif (Test-Path ".env.production") {
  ".env.production"
} else {
  $null
}

if ($EnvFile) {
  Write-Host "[migrate] Loading $EnvFile"
  Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $parts = $_.Split('=', 2)
    if ($parts.Length -eq 2) {
      [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim())
    }
  }
} else {
  Write-Host "[migrate] No .env / .env.production found; using process environment."
}

Write-Host "[migrate] Upgrading database to Alembic head..."
uv run alembic -c backend/alembic.ini upgrade head
Write-Host "[migrate] Current revision:"
uv run alembic -c backend/alembic.ini current
Write-Host "[migrate] Done."
