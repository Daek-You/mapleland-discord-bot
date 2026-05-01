"""Application entry point for the MapleLand Discord bot."""

from collections.abc import Callable

from dotenv import load_dotenv

from app.bot.client import MapleLandDiscordClient, create_discord_client
from app.config import get_required_discord_token
from app.logging_config import configure_logging


def main(
    client_factory: Callable[[], MapleLandDiscordClient] = create_discord_client,
) -> None:
    """Start the Discord bot."""
    load_dotenv()
    configure_logging()
    token = get_required_discord_token()
    client = client_factory()
    client.run(token)


if __name__ == "__main__":
    main()
