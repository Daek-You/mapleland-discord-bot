"""Discord slash commands for stored Mapleland feed categories."""

from __future__ import annotations

import discord
from discord import app_commands

from app.services.feed_query_service import FeedRepository, get_latest_feed_message


def register_feed_commands(command_tree: app_commands.CommandTree, repository: FeedRepository) -> None:
    """Register latest notice and event commands backed by normalized storage."""

    @command_tree.command(name="소식", description="저장된 최신 메이플랜드 소식을 보여줍니다.")
    async def news(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(
            await get_latest_feed_message(repository, category="notice", heading="Latest notices")
        )

    @command_tree.command(name="이벤트", description="저장된 최신 메이플랜드 이벤트를 보여줍니다.")
    async def events(interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(
            await get_latest_feed_message(repository, category="event", heading="Latest events")
        )
