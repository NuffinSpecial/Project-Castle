# Download cloudflared for Windows into scripts/.bin (no admin required).
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$binDir = Join-Path $PSScriptRoot ".bin"
$exe = Join-Path $binDir "cloudflared.exe"

New-Item -ItemType Directory -Force -Path $binDir | Out-Null

if (Test-Path $exe) {
  & $exe --version
  Write-Host "Already installed at: $exe"
  exit 0
}

$version = "2026.5.1"
$url = "https://github.com/cloudflare/cloudflared/releases/download/$version/cloudflared-windows-amd64.exe"
Write-Host "Downloading cloudflared $version …"
Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing

& $exe --version
Write-Host ""
Write-Host "Installed: $exe"
Write-Host "Run: .\scripts\cloudflare_tunnel.ps1"
