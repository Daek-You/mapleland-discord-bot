"""Discord slash command registration for ping."""

import discord
from discord import app_commands

from app.services.ping_service import get_ping_response


def register_ping_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /ping command."""

    @command_tree.command(name="ping", description="Check whether the bot is responsive.")
    async def ping(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(get_ping_response())
