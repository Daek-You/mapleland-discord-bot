"""Discord slash command registration for notice notification testing."""

import logging

import discord
from discord import app_commands

from app.bot.command_config import NOTIFICATION_TEST_COMMAND
from app.services.notification_service import (
    collect_test_notice_notifications,
    format_notice_notification,
)


logger = logging.getLogger(__name__)


def register_notification_test_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /알림테스트 command."""

    @command_tree.command(
        name=NOTIFICATION_TEST_COMMAND.name,
        description=NOTIFICATION_TEST_COMMAND.description,
    )
    async def notification_test(interaction: discord.Interaction) -> None:
        logger.info("/알림테스트 command executed.")
        try:
            notifications = collect_test_notice_notifications(str(interaction.id))
            message = "\n\n".join(
                format_notice_notification(notification) for notification in notifications
            )
            await interaction.response.send_message(message)
        except discord.HTTPException:
            logger.error("Failed to send /알림테스트 response.", exc_info=True)
            raise
        except Exception:
            logger.error("/알림테스트 command failed.", exc_info=True)
            raise
