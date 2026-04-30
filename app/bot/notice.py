"""Discord slash command registration for Mapleland notices."""

import discord
from discord import app_commands

from app.bot.command_config import NOTICE_COMMAND
from app.services.notice_service import get_latest_notice_message


def register_notice_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /공지 command."""

    @command_tree.command(name=NOTICE_COMMAND.name, description=NOTICE_COMMAND.description)
    async def notice(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(get_latest_notice_message())
