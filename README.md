# mapleland-discord-bot
Discord bot for MapleLand notices, summaries, and Q&amp;A

## Development

See [docs/development.md](docs/development.md) and [docs/testing.md](docs/testing.md) for the Docker-based build and test workflow.

## Operations

See [docs/operations.md](docs/operations.md) for separated development and production Docker Compose files, environment files, CI, Windows self-hosted runner deployment, restart behavior, startup registration, and log checks.

## Commands

Holy Symbol timer commands:

```text
/홀심시작
/홀심중지
/홀심상태
```

The timer runs for 100 seconds until stopped. Reminders are sent only to the
user's private timer thread, 10 seconds before expiration and at expiration.

TODO:

* TTS notifications
* Additional buff timers
