"""Discord client configuration."""

import os

import discord
from discord import app_commands

from app.bot.notice import register_notice_command
from app.bot.ping import register_ping_command


class MapleLandDiscordClient(discord.Client):
    """Discord client for the MapleLand bot."""

    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.command_tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """Register and sync slash commands."""
        register_notice_command(self.command_tree)
        register_ping_command(self.command_tree)

        guild_id = os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.command_tree.copy_global_to(guild=guild)
            await self.command_tree.sync(guild=guild)
            return

        await self.command_tree.sync()


def create_discord_client() -> MapleLandDiscordClient:
    """Create the Discord client."""
    return MapleLandDiscordClient()
