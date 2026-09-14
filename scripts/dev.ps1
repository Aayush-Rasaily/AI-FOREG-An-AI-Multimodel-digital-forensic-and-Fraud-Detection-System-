# Native local backend helper (Windows) — no Docker.
# Usage:
#   .\scripts\dev.ps1              # check + migrate + start API
#   .\scripts\dev.ps1 -MigrateOnly
#   .\scripts\dev.ps1 -CheckOnly
param(
  [switch]$MigrateOnly,
  [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Import-DotEnv([string]$Path) {
  if (-not (Test-Path $Path)) { return }
  Get-Content $Path | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $parts = $_.Split('=', 2)
    if ($parts.Length -eq 2) {
      [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim())
    }
  }
}

if (Test-Path ".env") {
  Import-DotEnv ".env"
  Write-Host "[dev] Loaded .env"
} else {
  Write-Host "[dev] WARNING: .env missing. Copy .env.example to .env first."
}

Write-Host "[dev] Python:"
uv run python -c "import sys; print(sys.version.split()[0])"

$pgHost = "127.0.0.1"
$pgPort = 5432
try {
  $client = New-Object System.Net.Sockets.TcpClient
  $iar = $client.BeginConnect($pgHost, $pgPort, $null, $null)
  $ok = $iar.AsyncWaitHandle.WaitOne(2000, $false)
  if ($ok -and $client.Connected) {
    Write-Host "[dev] PostgreSQL reachable at ${pgHost}:${pgPort}"
  } else {
    Write-Host "[dev] ERROR: PostgreSQL not reachable at ${pgHost}:${pgPort}"
    Write-Host "      Install/start native PostgreSQL, create database ai_forge, then set DATABASE_URL in .env"
    if (-not $CheckOnly) { exit 1 }
  }
  $client.Close()
} catch {
  Write-Host "[dev] ERROR: PostgreSQL probe failed: $_"
  if (-not $CheckOnly) { exit 1 }
}

if ($CheckOnly) { exit 0 }

Write-Host "[dev] Running migrations..."
uv run alembic -c backend/alembic.ini upgrade head
uv run alembic -c backend/alembic.ini current

if ($MigrateOnly) { exit 0 }

Write-Host "[dev] Starting API on http://127.0.0.1:8000 (Ctrl+C to stop)"
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
