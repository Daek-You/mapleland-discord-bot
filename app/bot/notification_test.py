"""Discord slash command registration for notice notification testing."""

import discord
from discord import app_commands

from app.bot.command_config import NOTIFICATION_TEST_COMMAND
from app.services.notification_service import (
    collect_test_notice_notifications,
    format_notice_notification,
)


def register_notification_test_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /알림테스트 command."""

    @command_tree.command(
        name=NOTIFICATION_TEST_COMMAND.name,
        description=NOTIFICATION_TEST_COMMAND.description,
    )
    async def notification_test(interaction: discord.Interaction) -> None:
        notifications = collect_test_notice_notifications(str(interaction.id))
        message = "\n\n".join(
            format_notice_notification(notification) for notification in notifications
        )
        await interaction.response.send_message(message)
