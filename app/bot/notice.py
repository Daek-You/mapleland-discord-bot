"""Discord slash command registration for Mapleland notices."""

import discord
from discord import app_commands

from app.services.notice_service import get_latest_notice_message


def register_notice_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /공지 command."""

    @command_tree.command(name="공지", description="최신 메이플랜드 공지사항 5개를 보여줍니다.")
    async def notice(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(get_latest_notice_message())
