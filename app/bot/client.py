"""Discord client configuration."""

import asyncio
import logging

import discord
from discord import app_commands

from app.bot.notification_test import register_notification_test_command
from app.bot.notice import register_notice_command
from app.bot.ping import register_ping_command
from app.config import (
    get_discord_guild_id,
    get_notice_channel_id,
    get_notice_check_interval_seconds,
)
from app.db.notice_repository import create_default_notice_repository
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
        self.notice_repository = create_default_notice_repository()
        self.notice_notification_task: asyncio.Task[None] | None = None

    async def setup_hook(self) -> None:
        """Register and sync slash commands."""
        register_notification_test_command(self.command_tree)
        register_notice_command(self.command_tree)
        register_ping_command(self.command_tree)
        self.notice_notification_task = asyncio.create_task(
            self._run_notice_notification_loop()
        )

        guild_id = get_discord_guild_id()
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.command_tree.copy_global_to(guild=guild)
            await self.command_tree.sync(guild=guild)
            return

        await self.command_tree.sync()

    async def close(self) -> None:
        """Stop background tasks before closing the Discord client."""
        if self.notice_notification_task:
            self.notice_notification_task.cancel()
        await super().close()

    async def _run_notice_notification_loop(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            await self.send_new_notice_notifications()
            await asyncio.sleep(get_notice_check_interval_seconds())

    async def send_new_notice_notifications(self) -> None:
        """Send newly detected notice notifications to the configured channel."""
        channel_id = get_notice_channel_id()
        if not channel_id:
            logger.info("NOTICE_CHANNEL_ID is not set. Skipping notice notification.")
            return

        channel = self.get_channel(int(channel_id)) or await self.fetch_channel(
            int(channel_id)
        )
        notifications = await asyncio.to_thread(
            collect_new_notice_notifications,
            notice_repository=self.notice_repository,
        )
        for notification in notifications:
            await channel.send(format_notice_notification(notification))


def create_discord_client() -> MapleLandDiscordClient:
    """Create the Discord client."""
    return MapleLandDiscordClient()
