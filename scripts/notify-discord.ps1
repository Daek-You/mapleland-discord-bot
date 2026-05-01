param(
    [Parameter(Mandatory = $true)]
    [string]$Message,
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

function Import-LocalEnv {
    param([string]$Root)

    $envPath = Join-Path $Root ".env"
    if (-not (Test-Path -LiteralPath $envPath)) {
        return
    }

    foreach ($line in Get-Content -LiteralPath $envPath -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }

        $name, $value = $trimmed.Split("=", 2)
        if (-not [Environment]::GetEnvironmentVariable($name, "Process")) {
            [Environment]::SetEnvironmentVariable($name, $value.Trim('"'), "Process")
        }
    }
}

function Send-DiscordNotification {
    param([string]$Content)

    $webhookUrl = $env:DISCORD_DEPLOY_WEBHOOK_URL
    if (-not $webhookUrl) {
        $webhookUrl = $env:DISCORD_ALERT_WEBHOOK_URL
    }
    if (-not $webhookUrl) {
        Write-Output "Discord operational webhook is not set. Skipping notification."
        return
    }

    $appEnv = if ($env:APP_ENV) { $env:APP_ENV } else { "production" }
    $botName = if ($env:BOT_NAME) { $env:BOT_NAME } else { "mapleland-discord-bot" }
    $payload = @{ content = "[$appEnv] ${botName}: $Content" } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri $webhookUrl -Method Post -Body $payload -ContentType "application/json" | Out-Null
    }
    catch {
        Write-Warning "Failed to send Discord operational notification: $($_.Exception.Message)"
    }
}

Import-LocalEnv -Root $ProjectRoot
Send-DiscordNotification -Content $Message
