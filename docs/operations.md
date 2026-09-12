# Operations Guide

## Environment Files

Development and production use separate environment files.

Development:

```text
.env
.env.example
```

Production:

```text
.env.production
.env.production.example
docker-compose.prod.yml
```

Do not commit real token, webhook, channel, guild, or API key values. `.env` and `.env.production` are ignored by Git.

Production variables:

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
DELIVERY_DISPATCH_INTERVAL_SECONDS=15
NOTICE_DATABASE_PATH=data/notices.sqlite3
LOG_LEVEL=INFO
LOG_TIMEZONE=Asia/Seoul
```

## Development Run

Run tests locally with uv. Docker Desktop is not required for the normal development
loop:

```powershell
uv sync --locked
uv run --locked pytest -p no:cacheprovider -v
```

Run the bot locally after setting `.env`:

```powershell
uv run --locked python -m app.main
```


## SQLite Migrations and Backups

The repository applies numbered SQL files from `app/db/migrations` when it opens the
database. Applied versions are recorded in `schema_migrations`, so each migration runs
only once.

When an existing database has a pending migration, a consistent copy is created with
SQLite's backup API before any schema change. By default, backups are stored next to
the database under `backups/` with a UTC timestamp in the filename.

To restore a backup, stop the bot first, preserve the failed database for diagnosis,
copy the selected backup to `NOTICE_DATABASE_PATH`, and restart the bot. Never replace
a live database file while the process is running.

## CI Runner

`.github/workflows/ci.yml` runs tests on GitHub-hosted `ubuntu-latest`.

It is for verification only:

* no production secrets
* no deployment
* no self-hosted runner requirement

## Production Host Setup

Install these on the production Windows PC:

* Git
* Docker Desktop
* GitHub Actions self-hosted runner

Python and uv do not need to be installed on the Windows host. They run inside the Docker image.

Enable Docker Desktop's start-on-login option so containers can come back after Windows restarts.

Clone the repository and create `.env.production` from `.env.production.example`. Fill values only on the host.

Build and test the production image:

```powershell
docker compose -f docker-compose.prod.yml build app
docker compose run --rm app uv run pytest
```

Start the production bot container:

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

## Production Runner

The deploy workflow requires a self-hosted Windows runner with these labels:

```text
self-hosted
Windows
production
```

The extra `production` label prevents development or test runners from accidentally picking up production deploy jobs.

Install the GitHub Actions runner as a Windows service from the runner directory:

```powershell
.\svc.cmd install
.\svc.cmd start
```

GitHub does not connect inbound to the production PC. The self-hosted runner keeps an outbound connection to GitHub, so fixed IP, DDNS, port forwarding, and firewall inbound rules are not required.

## Windows Startup

The production container uses Docker Compose `restart: unless-stopped`.

For reboot recovery:

1. Turn on Docker Desktop start-on-login.
2. Register the project startup task as a backup launcher:

```powershell
.\scripts\register-startup-task.ps1
```

This keeps the bot available after a Windows reboot.

If the production clone is not the same directory as the GitHub Actions workspace, set a repository Actions variable named `PRODUCTION_PROJECT_ROOT` to the absolute production path, for example `C:\apps\mapleland-discord-bot`.

## Deployment Flow

1. A push or PR merge updates `main`.
2. GitHub Actions starts `deploy.yml`.
3. A self-hosted Windows runner with the `production` label picks up the job.
4. `scripts/deploy.ps1` checks for `.env.production`.
5. The script fetches and fast-forwards `main`.
6. Docker Compose rebuilds with `docker-compose.prod.yml`.
7. Docker Compose starts or recreates the bot container.
8. Discord webhook notifications report deploy start, success, or failure.

## Process Supervision

Docker Compose runs the bot with `restart: unless-stopped`. If the bot process exits unexpectedly, Docker restarts the container.

Check production container status:

```powershell
docker compose -f docker-compose.prod.yml ps app
```

## Holy Symbol Timer TTS

Holy Symbol timer reminders are sent only to the user's private timer thread as Discord chat TTS messages. The bot does not join voice channels.

To hear voice reminders, enable Discord's setting for allowing playback and use of `/tts` commands:

```text
User Settings -> Notifications -> Advanced -> Allow playback and usage of /tts command
```

The "Read all messages aloud" option does not need to be enabled. To hear the voice reminder, keep the timer thread channel open in Discord.

For more natural playback, users can adjust:

```text
Accessibility -> Audio and Screen Reader -> Text-to-Speech Rate
```

Known Holy Symbol timer error cases:

* If `/홀심시작` returns "현재 채널에는 메랜도우미가 없어요. 메랜도우미가 있는 채널에서 다시 시도해주세요.", the bot cannot create the private timer thread in the current channel. Run the command in a channel where the bot is present and has permission to create private threads.

## Logs

Container logs:

```powershell
docker compose -f docker-compose.prod.yml logs -f app
```

Application file logs:

```text
logs/bot.log
```

GitHub Actions deployment output is available in the repository Actions tab. Do not print secrets in workflow or script output.

## Incident Checklist

Check these in order:

* GitHub Actions job result and deploy step output
* The production runner is online and has the `production` label
* `docker compose -f docker-compose.prod.yml ps app`
* `docker compose -f docker-compose.prod.yml logs --tail=100 app`
* `logs/bot.log`
* Windows Task Scheduler history for `MapleLandDiscordBot`
* Docker Desktop is running
* GitHub runner service status
* `.env.production` exists on the host and includes required values
* `DISCORD_ALERT_WEBHOOK_URL` or `DISCORD_DEPLOY_WEBHOOK_URL` is valid
