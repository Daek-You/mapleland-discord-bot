param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot
$env:APP_ENV = if ($env:APP_ENV) { $env:APP_ENV } else { "production" }
$productionEnvPath = Join-Path $ProjectRoot ".env.production"

function New-UnicodeMessage {
    param([int[]]$CodePoints)

    return -join ($CodePoints | ForEach-Object { [char]$_ })
}

$deployStartMessage = New-UnicodeMessage @(0xC0C8, 0x20, 0xBC84, 0xC804, 0xC73C, 0xB85C, 0x20, 0xC5C5, 0xB370, 0xC774, 0xD2B8, 0xD558, 0xB294, 0x20, 0xC911, 0xC774, 0xC5D0, 0xC694, 0x2E)
$deploySuccessMessage = New-UnicodeMessage @(0xC5C5, 0xB370, 0xC774, 0xD2B8, 0xAC00, 0x20, 0xC644, 0xB8CC, 0xB410, 0xC5B4, 0xC694, 0x2E)
$deployFailureMessage = New-UnicodeMessage @(0xC5C5, 0xB370, 0xC774, 0xD2B8, 0x20, 0xC911, 0x20, 0xBB38, 0xC81C, 0xAC00, 0x20, 0xBC1C, 0xC0DD, 0xD588, 0xC5B4, 0xC694, 0x2E, 0x20, 0xB85C, 0xADF8, 0xB97C, 0x20, 0xD655, 0xC778, 0xD574, 0xC8FC, 0xC138, 0xC694, 0x2E)

try {
    if (-not (Test-Path -LiteralPath $productionEnvPath)) {
        throw ".env.production is required for production deployment."
    }

    & "$PSScriptRoot\notify-discord.ps1" -ProjectRoot $ProjectRoot -Message $deployStartMessage
    git fetch --prune origin
    git checkout main
    git pull --ff-only origin main
    docker compose -f docker-compose.prod.yml build app
    docker compose -f docker-compose.prod.yml up -d app
    docker compose -f docker-compose.prod.yml ps app
    & "$PSScriptRoot\notify-discord.ps1" -ProjectRoot $ProjectRoot -Message $deploySuccessMessage
    Write-Output "Deployment completed."
}
catch {
    Write-Error $_
    & "$PSScriptRoot\notify-discord.ps1" -ProjectRoot $ProjectRoot -Message $deployFailureMessage
    exit 1
}
