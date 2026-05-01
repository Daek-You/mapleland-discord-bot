param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot

docker compose stop app

Write-Output "Bot container stop requested."
