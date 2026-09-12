"""Discord client configuration."""

import asyncio
import logging
from functools import partial

import discord
from discord import app_commands

from app.bot.feed import register_feed_commands
from app.bot.feed_subscription import register_feed_subscription_commands
from app.bot.holy_symbol import register_holy_symbol_commands
from app.bot.monster import register_monster_command
from app.bot.notice import register_notice_command
from app.bot.notification_test import register_notification_test_command
from app.bot.ping import register_ping_command
from app.config import (
    get_delivery_dispatch_interval_seconds,
    get_discord_guild_id,
    get_notice_channel_id,
    get_notice_check_interval_seconds,
)
from app.crawler.mapleland import (
    fetch_latest_devlog_items,
    fetch_latest_event_items,
    fetch_latest_notice_items,
)
from app.crawler.maplenote import fetch_monster_detail, search_monster_summaries
from app.db.delivery_repository import DeliveryRecord, create_default_delivery_repository
from app.db.feed_repository import create_default_feed_repository
from app.db.notice_repository import create_default_notice_repository
from app.db.subscription_repository import create_default_subscription_repository
from app.http_client import create_shared_http_client
from app.services.delivery_service import PermanentDeliveryError, dispatch_ready_deliveries
from app.services.feed_ingestion_service import collect_mapleland_board_feed_updates
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
        self.delivery_repository = create_default_delivery_repository()
        self.feed_repository = create_default_feed_repository()
        self.subscription_repository = create_default_subscription_repository()
        self.notice_notification_task: asyncio.Task[None] | None = None
        self.delivery_dispatch_task: asyncio.Task[None] | None = None
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
        register_feed_subscription_commands(
            self.command_tree,
            self.subscription_repository,
        )
        register_feed_commands(self.command_tree, self.feed_repository)
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
        self.delivery_dispatch_task = asyncio.create_task(
            self._run_delivery_dispatch_loop(),
            name="feed-delivery-dispatch-loop",
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
            if self.delivery_dispatch_task:
                self.delivery_dispatch_task.cancel()
                await asyncio.gather(
                    self.delivery_dispatch_task,
                    return_exceptions=True,
                )
                self.delivery_dispatch_task = None
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
        await self.collect_latest_feed_updates()
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

    async def collect_latest_feed_updates(self) -> None:
        """Collect official boards into the normalized feed and delivery queue."""
        await asyncio.gather(
            self._collect_mapleland_board_feed("notice", fetch_latest_notice_items),
            self._collect_mapleland_board_feed("event", fetch_latest_event_items),
            self._collect_mapleland_board_feed("devlog", fetch_latest_devlog_items),
        )

    async def _collect_mapleland_board_feed(self, category: str, fetch_board_items) -> None:
        await collect_mapleland_board_feed_updates(
            partial(fetch_board_items, client=self.http_client),
            category=category,
            feed_repository=self.feed_repository,
            subscription_repository=self.subscription_repository,
            delivery_repository=self.delivery_repository,
        )

    async def _run_delivery_dispatch_loop(self) -> None:
        """Dispatch queued feed revisions after the client becomes ready."""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self.send_pending_feed_deliveries()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error("Unexpected error in feed delivery dispatch loop.", exc_info=True)
            await asyncio.sleep(get_delivery_dispatch_interval_seconds())

    async def send_pending_feed_deliveries(self) -> None:
        """Send one queued delivery batch and record its outcome."""
        await dispatch_ready_deliveries(
            self.delivery_repository,
            self._send_feed_delivery_to_discord,
        )

    async def _send_feed_delivery_to_discord(self, delivery: DeliveryRecord) -> str:
        """Send one queued revision to its configured Discord channel."""
        try:
            channel = self.get_channel(int(delivery.channel_id))
            if channel is None:
                channel = await self.fetch_channel(int(delivery.channel_id))
            if not isinstance(channel, discord.abc.Messageable):
                raise PermanentDeliveryError("channel_not_messageable")
            message = await channel.send(_format_feed_delivery(delivery))
        except discord.NotFound as error:
            raise PermanentDeliveryError("channel_not_found") from error
        except discord.Forbidden as error:
            raise PermanentDeliveryError("channel_forbidden") from error
        return str(message.id)


def create_discord_client() -> MapleLandDiscordClient:
    """Create the Discord client."""
    return MapleLandDiscordClient()


def _format_feed_delivery(delivery: DeliveryRecord) -> str:
    """Format a revision notification with an optional configured role mention."""
    role_mention = f"<@&{delivery.role_id}>\n" if delivery.role_id else ""
    return f"{role_mention}**[{delivery.category}] {delivery.title}**\n{delivery.url}"
