param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot

docker compose up -d --build app

Write-Output "Bot container start requested."
