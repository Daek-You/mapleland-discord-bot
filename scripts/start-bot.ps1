param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot
$productionEnvPath = Join-Path $ProjectRoot ".env.production"

if (-not (Test-Path -LiteralPath $productionEnvPath)) {
    throw ".env.production is required for production startup."
}

docker compose -f docker-compose.prod.yml up -d --build app

Write-Output "Bot container start requested."
