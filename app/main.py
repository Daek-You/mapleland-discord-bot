"""Application entry point for the MapleLand Discord bot."""

import logging
from collections.abc import Callable

from dotenv import load_dotenv

from app.bot.client import MapleLandDiscordClient, create_discord_client
from app.config import get_required_discord_token, validate_runtime_config
from app.logging_config import configure_logging
from app.services.operational_notification_service import send_operational_notification

logger = logging.getLogger(__name__)


def main(
    client_factory: Callable[[], MapleLandDiscordClient] = create_discord_client,
) -> None:
    """Start the Discord bot."""
    load_dotenv()
    validate_runtime_config()
    configure_logging()
    send_operational_notification("봇이 시작되는 중이에요.")

    try:
        token = get_required_discord_token()
        client = client_factory()
        client.run(token)
    except Exception:
        logger.error("Discord bot stopped with an unexpected error.", exc_info=True)
        send_operational_notification("봇 실행 중 오류가 발생했어요. 로그를 확인해주세요.")
        raise
    finally:
        send_operational_notification("봇이 종료됐어요.")


if __name__ == "__main__":
    main()
