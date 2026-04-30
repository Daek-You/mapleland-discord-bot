"""Discord slash command registration for ping."""

import discord
from discord import app_commands

from app.bot.command_config import PING_COMMAND
from app.services.ping_service import get_ping_response


def register_ping_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /ping command."""

    @command_tree.command(name=PING_COMMAND.name, description=PING_COMMAND.description)
    async def ping(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(get_ping_response())
