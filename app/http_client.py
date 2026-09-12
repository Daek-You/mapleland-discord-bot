"""Shared outbound HTTP client configuration."""

import httpx

DEFAULT_HTTP_USER_AGENT = (
    "mapleland-discord-bot/0.1 "
    "(+https://github.com/Daek-You/mapleland-discord-bot)"
)


def create_shared_http_client() -> httpx.AsyncClient:
    """Create the process-wide client used for outbound crawler requests."""
    return httpx.AsyncClient(headers={"User-Agent": DEFAULT_HTTP_USER_AGENT})
