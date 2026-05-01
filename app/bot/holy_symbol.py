"""Discord slash command registration for Holy Symbol timers."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

import discord
from discord import app_commands

from app.bot.holy_symbol_command_config import (
    HOLY_SYMBOL_START_COMMAND,
    HOLY_SYMBOL_STATUS_COMMAND,
    HOLY_SYMBOL_STOP_COMMAND,
)
from app.config import (
    DEFAULT_HOLY_SYMBOL_THREAD_DELETE_DELAY_SECONDS,
    DEFAULT_HOLY_SYMBOL_THREAD_NAME_FORMAT,
)
from app.services.holy_symbol_timer_service import (
    HolySymbolTimerService,
    format_holy_symbol_start_response,
    format_holy_symbol_status_response,
    format_holy_symbol_stop_response,
    format_holy_symbol_thread_close_message,
    format_holy_symbol_thread_start_message,
    format_holy_symbol_thread_stop_message,
)


logger = logging.getLogger(__name__)


class ThreadNotifier:
    """Send timer notifications to a private Discord thread."""

    def __init__(
        self,
        thread: discord.abc.Messageable,
        delete_delay_seconds: int = DEFAULT_HOLY_SYMBOL_THREAD_DELETE_DELAY_SECONDS,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.thread = thread
        self.delete_delay_seconds = delete_delay_seconds
        self._sleep = sleep

    async def send(self, message: str) -> None:
        try:
            await self.thread.send(message)
        except (discord.NotFound, discord.HTTPException):
            logger.error("Failed to send Holy Symbol timer notification.", exc_info=True)

    async def close(self, message: str) -> None:
        await self.send(format_holy_symbol_thread_close_message(message))
        asyncio.create_task(self._delete_thread_after_delay())

    async def _delete_thread_after_delay(self) -> None:
        await self._sleep(self.delete_delay_seconds)
        try:
            await self.thread.delete()
        except discord.NotFound:
            logger.info("Holy Symbol timer thread was already deleted.")
        except discord.HTTPException:
            logger.error("Failed to delete Holy Symbol timer thread.", exc_info=True)
        except Exception:
            logger.error(
                "Unexpected failure while deleting Holy Symbol timer thread.",
                exc_info=True,
            )


def _format_thread_name(user: object) -> str:
    username = getattr(user, "display_name", None) or getattr(user, "name", str(user))
    return DEFAULT_HOLY_SYMBOL_THREAD_NAME_FORMAT.format(username=username)


def _is_thread_channel(channel: object) -> bool:
    return isinstance(channel, discord.Thread) or (
        hasattr(channel, "send") and hasattr(channel, "add_user")
    )


async def _fetch_thread(
    interaction: discord.Interaction,
    thread_id: int,
) -> object | None:
    guild = interaction.guild
    if guild:
        thread = guild.get_thread(thread_id)
        if thread:
            return thread

    client = interaction.client
    thread = client.get_channel(thread_id)
    if _is_thread_channel(thread):
        return thread

    try:
        fetched_channel = await client.fetch_channel(thread_id)
    except (discord.NotFound, discord.HTTPException):
        logger.info("Holy Symbol timer thread is unavailable. Creating a new thread.")
        return None

    if _is_thread_channel(fetched_channel):
        return fetched_channel
    return None


async def _create_private_thread(
    interaction: discord.Interaction,
) -> object:
    channel = interaction.channel
    if channel is None or not hasattr(channel, "create_thread"):
        raise RuntimeError("알림을 보낼 채널을 찾을 수 없습니다.")

    thread = await channel.create_thread(
        name=_format_thread_name(interaction.user),
        type=discord.ChannelType.private_thread,
        invitable=False,
    )
    await thread.add_user(interaction.user)
    return thread


async def _get_or_create_private_thread(
    interaction: discord.Interaction,
    existing_thread_id: int | None,
) -> object:
    if existing_thread_id is not None:
        thread = await _fetch_thread(interaction, existing_thread_id)
        if thread:
            return thread

    return await _create_private_thread(interaction)


def register_holy_symbol_commands(
    command_tree: app_commands.CommandTree,
    timer_service: HolySymbolTimerService,
    thread_delete_delay_seconds: int = DEFAULT_HOLY_SYMBOL_THREAD_DELETE_DELAY_SECONDS,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Register Holy Symbol timer commands."""

    @command_tree.command(
        name=HOLY_SYMBOL_START_COMMAND.name,
        description=HOLY_SYMBOL_START_COMMAND.description,
    )
    async def holy_symbol_start(interaction: discord.Interaction) -> None:
        logger.info("/홀심시작 command executed.")
        try:
            guild_id = interaction.guild_id or 0
            user_id = interaction.user.id
            existing_timer = timer_service.get_holy_symbol_timer(guild_id, user_id)
            thread = await _get_or_create_private_thread(
                interaction,
                existing_timer.thread_id if existing_timer else None,
            )
            notifier = ThreadNotifier(thread, thread_delete_delay_seconds, sleep)

            restarted = timer_service.start_holy_symbol_timer(
                guild_id=guild_id,
                user_id=user_id,
                thread_id=thread.id,
                notifier=notifier,
            )
            await notifier.send(
                format_holy_symbol_thread_start_message(timer_service.duration_seconds)
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
            guild_id = interaction.guild_id or 0
            user_id = interaction.user.id
            timer = timer_service.get_holy_symbol_timer(guild_id, user_id)
            stopped = timer_service.stop_holy_symbol_timer(
                guild_id=guild_id,
                user_id=user_id,
            )
            if stopped and timer:
                await timer.notifier.close(format_holy_symbol_thread_stop_message())
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
