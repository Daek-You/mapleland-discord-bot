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
DEFAULT_NOTICE_CHECK_INTERVAL_SECONDS = 600
DEFAULT_NOTICE_DATABASE_PATH = "data/notices.sqlite3"


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
