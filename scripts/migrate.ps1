# Apply Alembic migrations to head (Windows). Idempotent.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$EnvFile = if ($env:ENV_FILE) { $env:ENV_FILE } else { ".env.production" }
if (Test-Path $EnvFile) {
  Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $parts = $_.Split('=', 2)
    if ($parts.Length -eq 2) {
      [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim())
    }
  }
}

Write-Host "[migrate] Upgrading database to Alembic head..."
uv run --no-dev alembic -c backend/alembic.ini upgrade head
Write-Host "[migrate] Current revision:"
uv run --no-dev alembic -c backend/alembic.ini current
Write-Host "[migrate] Done."
