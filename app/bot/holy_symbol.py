"""Discord slash command registration for Holy Symbol timers."""

import logging

import discord
from discord import app_commands

from app.bot.holy_symbol_command_config import (
    HOLY_SYMBOL_START_COMMAND,
    HOLY_SYMBOL_STATUS_COMMAND,
    HOLY_SYMBOL_STOP_COMMAND,
)
from app.services.holy_symbol_timer_service import (
    HolySymbolTimerService,
    format_holy_symbol_start_response,
    format_holy_symbol_status_response,
    format_holy_symbol_stop_response,
)


logger = logging.getLogger(__name__)


class TextNotifier:
    """Send timer notifications as public channel messages."""

    def __init__(self, channel: discord.abc.Messageable) -> None:
        self.channel = channel

    async def send(self, message: str) -> None:
        try:
            await self.channel.send(message)
        except discord.HTTPException:
            logger.error("Failed to send Holy Symbol timer notification.", exc_info=True)


def register_holy_symbol_commands(
    command_tree: app_commands.CommandTree,
    timer_service: HolySymbolTimerService,
) -> None:
    """Register Holy Symbol timer commands."""

    @command_tree.command(
        name=HOLY_SYMBOL_START_COMMAND.name,
        description=HOLY_SYMBOL_START_COMMAND.description,
    )
    async def holy_symbol_start(interaction: discord.Interaction) -> None:
        logger.info("/홀심시작 command executed.")
        try:
            channel = interaction.channel
            if channel is None:
                await interaction.response.send_message(
                    "알림을 보낼 채널을 찾을 수 없습니다.",
                    ephemeral=True,
                )
                return

            restarted = timer_service.start_holy_symbol_timer(
                guild_id=interaction.guild_id or 0,
                user_id=interaction.user.id,
                notifier=TextNotifier(channel),
            )
            await interaction.response.send_message(
                format_holy_symbol_start_response(restarted),
                ephemeral=True,
            )
        except discord.HTTPException:
            logger.error("Failed to send /홀심시작 response.", exc_info=True)
            raise
        except Exception:
            logger.error("/홀심시작 command failed.", exc_info=True)
            raise

    @command_tree.command(
        name=HOLY_SYMBOL_STOP_COMMAND.name,
        description=HOLY_SYMBOL_STOP_COMMAND.description,
    )
    async def holy_symbol_stop(interaction: discord.Interaction) -> None:
        logger.info("/홀심중지 command executed.")
        try:
            stopped = timer_service.stop_holy_symbol_timer(
                guild_id=interaction.guild_id or 0,
                user_id=interaction.user.id,
            )
            await interaction.response.send_message(
                format_holy_symbol_stop_response(stopped),
                ephemeral=True,
            )
        except discord.HTTPException:
            logger.error("Failed to send /홀심중지 response.", exc_info=True)
            raise
        except Exception:
            logger.error("/홀심중지 command failed.", exc_info=True)
            raise

    @command_tree.command(
        name=HOLY_SYMBOL_STATUS_COMMAND.name,
        description=HOLY_SYMBOL_STATUS_COMMAND.description,
    )
    async def holy_symbol_status(interaction: discord.Interaction) -> None:
        logger.info("/홀심상태 command executed.")
        try:
            remaining_seconds = timer_service.get_holy_symbol_remaining_seconds(
                guild_id=interaction.guild_id or 0,
                user_id=interaction.user.id,
            )
            await interaction.response.send_message(
                format_holy_symbol_status_response(remaining_seconds),
                ephemeral=True,
            )
        except discord.HTTPException:
            logger.error("Failed to send /홀심상태 response.", exc_info=True)
            raise
        except Exception:
            logger.error("/홀심상태 command failed.", exc_info=True)
            raise
