"""Discord slash command registration for Mapleland notices."""

import logging

import discord
from discord import app_commands

from app.bot.command_config import NOTICE_COMMAND
from app.services.notice_service import get_latest_notice_message


logger = logging.getLogger(__name__)


def register_notice_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /공지 command."""

    @command_tree.command(name=NOTICE_COMMAND.name, description=NOTICE_COMMAND.description)
    async def notice(interaction: discord.Interaction) -> None:
        logger.info("/공지 command executed.")
        try:
            await interaction.response.defer(thinking=True)
            await interaction.followup.send(await get_latest_notice_message())
        except discord.HTTPException:
            logger.error("Failed to send /공지 response.", exc_info=True)
            raise
        except Exception:
            logger.error("/공지 command failed.", exc_info=True)
            raise
