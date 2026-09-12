"""Discord client configuration."""

import asyncio
import logging
from functools import partial

import discord
from discord import app_commands

from app.bot.holy_symbol import register_holy_symbol_commands
from app.bot.monster import register_monster_command
from app.bot.notice import register_notice_command
from app.bot.notification_test import register_notification_test_command
from app.bot.ping import register_ping_command
from app.config import (
    get_discord_guild_id,
    get_notice_channel_id,
    get_notice_check_interval_seconds,
)
from app.crawler.mapleland import fetch_latest_notice_items
from app.crawler.maplenote import fetch_monster_detail, search_monster_summaries
from app.db.notice_repository import create_default_notice_repository
from app.http_client import create_shared_http_client
from app.services.holy_symbol_timer_service import HolySymbolTimerService
from app.services.notification_service import (
    collect_new_notice_notifications,
    format_notice_notification,
)

logger = logging.getLogger(__name__)


class MapleLandDiscordClient(discord.Client):
    """Discord client for the MapleLand bot."""

    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.command_tree = app_commands.CommandTree(self)
        self.http_client = create_shared_http_client()
        self.notice_repository = create_default_notice_repository()
        self.notice_notification_task: asyncio.Task[None] | None = None
        self.holy_symbol_timer_service = HolySymbolTimerService()

    async def setup_hook(self) -> None:
        """Register and sync slash commands."""
        logger.info("Registering Discord slash commands.")
        register_monster_command(
            self.command_tree,
            search_summaries=partial(
                search_monster_summaries,
                client=self.http_client,
            ),
            get_detail=partial(
                fetch_monster_detail,
                client=self.http_client,
            ),
        )
        register_notification_test_command(self.command_tree)
        register_notice_command(
            self.command_tree,
            fetch_notice_items=partial(
                fetch_latest_notice_items,
                client=self.http_client,
            ),
        )
        register_ping_command(self.command_tree)
        register_holy_symbol_commands(
            self.command_tree,
            self.holy_symbol_timer_service,
        )
        guild_id = get_discord_guild_id()
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.command_tree.copy_global_to(guild=guild)
            try:
                await self.command_tree.sync(guild=guild)
            except discord.HTTPException:
                logger.error("Failed to sync Discord guild commands.", exc_info=True)
                raise
        else:
            try:
                await self.command_tree.sync()
            except discord.HTTPException:
                logger.error("Failed to sync Discord global commands.", exc_info=True)
                raise

        self.notice_notification_task = asyncio.create_task(
            self._run_notice_notification_loop(),
            name="notice-notification-loop",
        )

    async def close(self) -> None:
        """Stop background tasks before closing the Discord client."""
        try:
            if self.notice_notification_task:
                self.notice_notification_task.cancel()
                await asyncio.gather(
                    self.notice_notification_task,
                    return_exceptions=True,
                )
                self.notice_notification_task = None
            self.holy_symbol_timer_service.cancel_all()
        finally:
            try:
                await self.http_client.aclose()
            finally:
                await super().close()

    async def _run_notice_notification_loop(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self.send_new_notice_notifications()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error(
                    "Unexpected error in notice notification loop.",
                    exc_info=True,
                )
            await asyncio.sleep(get_notice_check_interval_seconds())

    async def send_new_notice_notifications(self) -> None:
        """Send newly detected notice notifications to the configured channel."""
        channel_id = get_notice_channel_id()
        if not channel_id:
            logger.info("NOTICE_CHANNEL_ID is not set. Skipping notice notification.")
            return

        try:
            channel = self.get_channel(int(channel_id)) or await self.fetch_channel(
                int(channel_id)
            )
        except discord.HTTPException:
            logger.error("Failed to fetch notice notification channel.", exc_info=True)
            return

        notifications = await collect_new_notice_notifications(
            fetch_notice_items=partial(
                fetch_latest_notice_items,
                client=self.http_client,
            ),
            notice_repository=self.notice_repository,
        )
        for notification in notifications:
            try:
                await channel.send(format_notice_notification(notification))
            except discord.HTTPException:
                logger.error("Failed to send notice notification.", exc_info=True)


def create_discord_client() -> MapleLandDiscordClient:
    """Create the Discord client."""
    return MapleLandDiscordClient()
