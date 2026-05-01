param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$NotifyDeployment
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot
$productionEnvPath = Join-Path $ProjectRoot ".env.production"

if (-not (Test-Path -LiteralPath $productionEnvPath)) {
    throw ".env.production is required for production restart."
}

function New-UnicodeMessage {
    param([int[]]$CodePoints)

    return -join ($CodePoints | ForEach-Object { [char]$_ })
}

$deployStartMessage = New-UnicodeMessage @(0xC0C8, 0x20, 0xBC84, 0xC804, 0xC73C, 0xB85C, 0x20, 0xC5C5, 0xB370, 0xC774, 0xD2B8, 0xD558, 0xB294, 0x20, 0xC911, 0xC774, 0xC5D0, 0xC694, 0x2E)
$deploySuccessMessage = New-UnicodeMessage @(0xC5C5, 0xB370, 0xC774, 0xD2B8, 0xAC00, 0x20, 0xC644, 0xB8CC, 0xB410, 0xC5B4, 0xC694, 0x2E)

if ($NotifyDeployment) {
    & "$PSScriptRoot\notify-discord.ps1" -ProjectRoot $ProjectRoot -Message $deployStartMessage
}

docker compose -f docker-compose.prod.yml up -d --build app

if ($NotifyDeployment) {
    & "$PSScriptRoot\notify-discord.ps1" -ProjectRoot $ProjectRoot -Message $deploySuccessMessage
}
