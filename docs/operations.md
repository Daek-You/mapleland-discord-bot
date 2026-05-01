# Operations Guide

## Environment

Runtime mode is selected with `APP_ENV`.

Use `development` for local work and `production` on the Windows host. Secrets must live only in `.env`, Windows environment variables, or GitHub Secrets.

Required or commonly used variables:

```text
APP_ENV=production
BOT_NAME=mapleland-discord-bot
DISCORD_TOKEN=
DISCORD_GUILD_ID=
DISCORD_ALERT_CHANNEL_ID=
DISCORD_ALERT_WEBHOOK_URL=
DISCORD_DEPLOY_WEBHOOK_URL=
NOTICE_CHANNEL_ID=
NOTICE_CHECK_INTERVAL_SECONDS=600
NOTICE_DATABASE_PATH=data/notices.sqlite3
LOG_LEVEL=INFO
LOG_TIMEZONE=Asia/Seoul
```

Do not commit real token, webhook, channel, guild, or API key values.

## Development Run

Run tests in Docker:

```powershell
docker compose run --rm app uv run pytest
```

Run the bot in Docker after setting `.env`:

```powershell
docker compose up -d --build app
docker compose logs -f app
```

Set `APP_ENV=development` in local `.env`.

## Production Host Setup

Install these on the friend's Windows PC:

* Git
* Docker Desktop
* GitHub Actions self-hosted runner

Python and uv do not need to be installed on the Windows host. They run inside the Docker image.

Enable Docker Desktop's start-on-login option so containers can come back after Windows restarts.

Clone the repository and create a local `.env` from `.env.example`. Fill values only on the host.

Build and test the container:

```powershell
docker compose build app
docker compose run --rm app uv run pytest
```

Start the bot container manually:

```powershell
.\scripts\start-bot.ps1
```

Restart manually:

```powershell
.\scripts\restart-bot.ps1
```

Stop manually:

```powershell
.\scripts\stop-bot.ps1
```

## Windows Startup

The bot container uses Docker Compose `restart: unless-stopped`.

For reboot recovery:

1. Turn on Docker Desktop start-on-login.
2. Register the project startup task as a backup launcher:

```powershell
.\scripts\register-startup-task.ps1
```

The GitHub Actions runner should also be installed as a Windows service from the runner directory:

```powershell
.\svc.cmd install
.\svc.cmd start
```

This keeps both the runner and bot available after a Windows reboot.

If the production clone is not the same directory as the GitHub Actions workspace, set a repository Actions variable named `PRODUCTION_PROJECT_ROOT` to the absolute production path, for example `C:\apps\mapleland-discord-bot`.

## Deployment Flow

1. A push or PR merge updates `main`.
2. GitHub Actions starts on the self-hosted Windows runner.
3. The runner checks out latest `main`.
4. `scripts/deploy.ps1` fetches and fast-forwards `main`.
5. Docker Compose rebuilds the app image.
6. Docker Compose starts or recreates the bot container.
7. Discord webhook notifications report deploy start, success, or failure.

GitHub does not connect inbound to the friend's PC. The self-hosted runner keeps an outbound connection to GitHub, so fixed IP, DDNS, port forwarding, and firewall inbound rules are not required.

## Process Supervision

Docker Compose runs the bot with `restart: unless-stopped`. If the bot process exits unexpectedly, Docker restarts the container.

Check container status:

```powershell
docker compose ps app
```

## Logs

Container logs:

```powershell
docker compose logs -f app
```

Application file logs:

```text
logs/bot.log
```

GitHub Actions deployment output is available in the repository Actions tab. Do not print secrets in workflow or script output.

## Incident Checklist

Check these in order:

* GitHub Actions job result and deploy step output
* `docker compose ps app`
* `docker compose logs --tail=100 app`
* `logs/bot.log`
* Windows Task Scheduler history for `MapleLandDiscordBot`
* Docker Desktop is running
* GitHub runner service status
* `.env` exists on the host and includes required values
* `DISCORD_ALERT_WEBHOOK_URL` or `DISCORD_DEPLOY_WEBHOOK_URL` is valid
