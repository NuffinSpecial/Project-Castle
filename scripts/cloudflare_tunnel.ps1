Param(
  [string]$Hostname = "",
  [string]$TunnelName = "project-castle",
  [string]$Port = "5000"
)

$ErrorActionPreference = "Stop"

function Resolve-Cloudflared {
  $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Source
  }

  $candidates = @(
    (Join-Path $PSScriptRoot ".bin\cloudflared.exe"),
    "$env:ProgramFiles\Cloudflare\cloudflared\cloudflared.exe",
    "${env:ProgramFiles(x86)}\Cloudflare\cloudflared\cloudflared.exe"
  )

  foreach ($path in $candidates) {
    if (Test-Path $path) {
      return $path
    }
  }

  Write-Host "cloudflared not found."
  Write-Host "  1) Close this terminal, open a NEW one, then run: cloudflared --version"
  Write-Host "  2) Or install locally (no admin): .\scripts\install_cloudflared.ps1"
  Write-Host "  3) Or: winget install Cloudflare.cloudflared  (then open a NEW terminal)"
  throw "cloudflared is required."
}

Set-Location (Split-Path -Parent $PSScriptRoot)

$cloudflared = Resolve-Cloudflared
Write-Host "Using cloudflared: $cloudflared"

Write-Host "Starting Project Castle locally..."
$app = Start-Process -PassThru -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList "/c", "dev.bat"

Write-Host "Waiting for local server to start..."
Start-Sleep -Seconds 3

Write-Host "Starting Cloudflare Tunnel..."
$target = "http://127.0.0.1:$Port"

if ($Hostname -ne "") {
  Write-Host "Using named tunnel: $TunnelName (hostname: $Hostname)"
  & $cloudflared tunnel run --url $target $TunnelName
} else {
  Write-Host "Quick tunnel (random public URL; no domain needed)."
  & $cloudflared tunnel --url $target
}

try {
  if ($app -and -not $app.HasExited) {
    Stop-Process -Id $app.Id -Force
  }
} catch {
  # ignore
}
