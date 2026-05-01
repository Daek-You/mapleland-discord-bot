"""Application configuration helpers.

Runtime values still come from environment variables such as `.env`.
This module keeps safe defaults and environment keys in one place.
"""

import os


DISCORD_TOKEN_ENV_NAME = "DISCORD_TOKEN"
DISCORD_GUILD_ID_ENV_NAME = "DISCORD_GUILD_ID"
NOTICE_CHANNEL_ID_ENV_NAME = "NOTICE_CHANNEL_ID"
NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME = "NOTICE_CHECK_INTERVAL_SECONDS"
NOTICE_DATABASE_PATH_ENV_NAME = "NOTICE_DATABASE_PATH"
LOG_LEVEL_ENV_NAME = "LOG_LEVEL"
LOG_TIMEZONE_ENV_NAME = "LOG_TIMEZONE"
APP_ENV_ENV_NAME = "APP_ENV"
BOT_NAME_ENV_NAME = "BOT_NAME"
DISCORD_ALERT_WEBHOOK_URL_ENV_NAME = "DISCORD_ALERT_WEBHOOK_URL"
DISCORD_ALERT_CHANNEL_ID_ENV_NAME = "DISCORD_ALERT_CHANNEL_ID"

MAPLELAND_NOTICE_LIST_URL = "https://maple.land/board/notices"
MAPLELAND_NOTICE_PATH_PREFIX = "/board/notices/"
MAPLENOTE_BASE_URL = "https://xn--o80b01o9mlw3kdzc.com"
MAPLENOTE_MONSTER_LIST_URL = f"{MAPLENOTE_BASE_URL}/monsters"

DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_MAPLENOTE_REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_NOTICE_DISPLAY_LIMIT = 5
DEFAULT_MONSTER_CANDIDATE_DISPLAY_LIMIT = 5
DEFAULT_MONSTER_DROP_DISPLAY_LIMIT = 10
DEFAULT_MONSTER_DROP_PAGE_SIZE = 7
DEFAULT_MONSTER_DROP_PAGINATION_TIMEOUT_SECONDS = 180
DEFAULT_MONSTER_SPAWN_DISPLAY_LIMIT = 10
DEFAULT_MONSTER_EMBED_COLOR = 0x2ECC71
DEFAULT_HOLY_SYMBOL_TIMER_TYPE = "HOLY_SYMBOL"
DEFAULT_HOLY_SYMBOL_DURATION_SECONDS = 100
DEFAULT_HOLY_SYMBOL_WARNING_BEFORE_EXPIRATION_SECONDS = 10
DEFAULT_HOLY_SYMBOL_THREAD_NAME_FORMAT = "{username}-홀심"
DEFAULT_HOLY_SYMBOL_THREAD_DELETE_DELAY_SECONDS = 10
DEFAULT_NOTICE_CHECK_INTERVAL_SECONDS = 600
DEFAULT_NOTICE_DATABASE_PATH = "data/notices.sqlite3"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_TIMEZONE = "Asia/Seoul"
DEFAULT_LOG_FILE_PATH = "logs/bot.log"
DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_LOG_BACKUP_COUNT = 5
DEFAULT_APP_ENV = "development"
DEFAULT_BOT_NAME = "mapleland-discord-bot"
VALID_APP_ENVS = {"development", "production"}


def get_required_discord_token() -> str:
    """Return the Discord token from the environment."""
    token = os.getenv(DISCORD_TOKEN_ENV_NAME)
    if not token:
        raise RuntimeError(
            f"{DISCORD_TOKEN_ENV_NAME} is required. Set it in .env or the environment."
        )
    return token


def get_discord_guild_id() -> str | None:
    """Return the Discord guild id configured for local command sync."""
    return os.getenv(DISCORD_GUILD_ID_ENV_NAME)


def get_notice_channel_id() -> str | None:
    """Return the Discord channel id for notice notifications."""
    return os.getenv(NOTICE_CHANNEL_ID_ENV_NAME)


def get_notice_check_interval_seconds() -> int:
    """Return notice check interval from the environment."""
    raw_interval = os.getenv(NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME)
    if not raw_interval:
        return DEFAULT_NOTICE_CHECK_INTERVAL_SECONDS
    return int(raw_interval)


def get_notice_database_path() -> str:
    """Return the notice database path."""
    return os.getenv(NOTICE_DATABASE_PATH_ENV_NAME) or DEFAULT_NOTICE_DATABASE_PATH


def get_log_level() -> str:
    """Return the configured logging level name."""
    return os.getenv(LOG_LEVEL_ENV_NAME) or DEFAULT_LOG_LEVEL


def get_log_timezone() -> str:
    """Return the configured IANA timezone name for log timestamps."""
    return os.getenv(LOG_TIMEZONE_ENV_NAME) or DEFAULT_LOG_TIMEZONE


def get_app_env() -> str:
    """Return the configured application environment."""
    app_env = (os.getenv(APP_ENV_ENV_NAME) or DEFAULT_APP_ENV).lower()
    if app_env not in VALID_APP_ENVS:
        raise RuntimeError(
            f"{APP_ENV_ENV_NAME} must be one of: {', '.join(sorted(VALID_APP_ENVS))}."
        )
    return app_env


def get_bot_name() -> str:
    """Return the display name used in operational notifications."""
    return os.getenv(BOT_NAME_ENV_NAME) or DEFAULT_BOT_NAME


def get_discord_alert_webhook_url() -> str | None:
    """Return the Discord webhook URL for operational alerts."""
    return os.getenv(DISCORD_ALERT_WEBHOOK_URL_ENV_NAME)


def get_discord_alert_channel_id() -> str | None:
    """Return the Discord channel id reserved for operational alerts."""
    return os.getenv(DISCORD_ALERT_CHANNEL_ID_ENV_NAME)
