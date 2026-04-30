"""Discord slash command registration for monster search."""

import discord
from discord import app_commands

from app.bot.command_config import MONSTER_COMMAND, MONSTER_DROP_COMMAND
from app.config import DEFAULT_MONSTER_EMBED_COLOR
from app.services.monster_service import (
    MonsterEmbedData,
    get_monster_drop_search_response,
    get_monster_search_response,
)


def register_monster_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /몬스터 command."""

    @command_tree.command(name=MONSTER_COMMAND.name, description=MONSTER_COMMAND.description)
    @app_commands.rename(name="이름")
    @app_commands.describe(name="검색할 몬스터 이름")
    async def monster(interaction: discord.Interaction, name: str) -> None:
        response = get_monster_search_response(name)
        if response.embed:
            await interaction.response.send_message(
                content=response.content,
                embed=_create_monster_embed(response.embed),
            )
            return

        await interaction.response.send_message(response.content)

    @command_tree.command(
        name=MONSTER_DROP_COMMAND.name,
        description=MONSTER_DROP_COMMAND.description,
    )
    @app_commands.rename(name="이름")
    @app_commands.describe(name="드랍 정보를 검색할 몬스터 이름")
    async def monster_drop(interaction: discord.Interaction, name: str) -> None:
        response = get_monster_drop_search_response(name)
        if response.embeds:
            await interaction.response.send_message(
                content=response.content,
                embeds=[
                    _create_monster_embed(embed_data)
                    for embed_data in response.embeds
                ],
            )
            return

        await interaction.response.send_message(response.content)


def _create_monster_embed(embed_data: MonsterEmbedData) -> discord.Embed:
    embed = discord.Embed(
        title=embed_data.title,
        description=embed_data.description,
        url=embed_data.url,
        color=DEFAULT_MONSTER_EMBED_COLOR,
    )
    if embed_data.thumbnail_url:
        embed.set_thumbnail(url=embed_data.thumbnail_url)
    for field in embed_data.fields:
        embed.add_field(name=field.name, value=field.value, inline=field.inline)
    if embed_data.footer:
        embed.set_footer(text=embed_data.footer)
    return embed
