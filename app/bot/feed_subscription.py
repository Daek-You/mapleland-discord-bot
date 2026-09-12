"""Administrator slash commands for feed category subscriptions."""

from __future__ import annotations

import discord
from discord import app_commands

from app.services.subscription_service import (
    SubscriptionRepository,
    subscribe_to_feed,
    unsubscribe_from_feed,
)

SUPPORTED_FEED_CATEGORIES = ("notice", "event", "devlog")


def register_feed_subscription_commands(
    command_tree: app_commands.CommandTree,
    subscription_repository: SubscriptionRepository,
) -> None:
    """Register administrator-only commands to manage feed delivery targets."""

    @command_tree.command(name="subscribe", description="Subscribe this channel to a feed category.")
    async def subscribe(
        interaction: discord.Interaction,
        category: str,
        channel: discord.TextChannel | None = None,
        role: discord.Role | None = None,
    ) -> None:
        if not _has_manage_guild_permission(interaction):
            await interaction.response.send_message(
                "You need Manage Server permission to change subscriptions.",
                ephemeral=True,
            )
            return
        if category not in SUPPORTED_FEED_CATEGORIES:
            await interaction.response.send_message(
                "Unsupported category. Use notice, event, or devlog.",
                ephemeral=True,
            )
            return
        target_channel_id = str(channel.id if channel else interaction.channel_id)
        await subscribe_to_feed(
            subscription_repository,
            category=category,
            channel_id=target_channel_id,
            role_id=str(role.id) if role else None,
        )
        await interaction.response.send_message(
            f"Subscribed <#{target_channel_id}> to {category}.",
            ephemeral=True,
        )

    @command_tree.command(name="unsubscribe", description="Unsubscribe this channel from a feed category.")
    async def unsubscribe(
        interaction: discord.Interaction,
        category: str,
        channel: discord.TextChannel | None = None,
    ) -> None:
        if not _has_manage_guild_permission(interaction):
            await interaction.response.send_message(
                "You need Manage Server permission to change subscriptions.",
                ephemeral=True,
            )
            return
        target_channel_id = str(channel.id if channel else interaction.channel_id)
        was_enabled = await unsubscribe_from_feed(
            subscription_repository,
            category=category,
            channel_id=target_channel_id,
        )
        message = (
            f"Unsubscribed <#{target_channel_id}> from {category}."
            if was_enabled
            else f"No active {category} subscription exists for <#{target_channel_id}>."
        )
        await interaction.response.send_message(message, ephemeral=True)


def _has_manage_guild_permission(interaction: discord.Interaction) -> bool:
    """Return whether the interaction came from a server manager."""
    guild_permissions = getattr(interaction.user, "guild_permissions", None)
    return bool(guild_permissions and guild_permissions.manage_guild)
