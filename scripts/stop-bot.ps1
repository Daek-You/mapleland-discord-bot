param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot

docker compose -f docker-compose.prod.yml stop app

Write-Output "Bot container stop requested."
