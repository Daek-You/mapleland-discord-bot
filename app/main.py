"""Application entry point for the MapleLand Discord bot."""

import os
from collections.abc import Callable

from dotenv import load_dotenv

from app.bot.client import MapleLandDiscordClient, create_discord_client


def get_required_discord_token() -> str:
    """Return the Discord token from the environment."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is required. Set it in .env or the environment.")
    return token


def main(
    client_factory: Callable[[], MapleLandDiscordClient] = create_discord_client,
) -> None:
    """Start the Discord bot."""
    load_dotenv()
    token = get_required_discord_token()
    client = client_factory()
    client.run(token)


if __name__ == "__main__":
    main()
