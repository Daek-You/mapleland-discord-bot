"""Discord slash command registration for monster search."""

import logging
import math
import secrets

import discord
from discord import app_commands

from app.bot.command_config import MONSTER_COMMAND, MONSTER_DROP_COMMAND
from app.config import (
    DEFAULT_MONSTER_DROP_PAGE_SIZE,
    DEFAULT_MONSTER_DROP_PAGINATION_TIMEOUT_SECONDS,
    DEFAULT_MONSTER_EMBED_COLOR,
)
from app.crawler.maplenote import MonsterDropItem
from app.services.monster_service import (
    MonsterEmbedData,
    get_monster_drop_search_response,
    get_monster_search_response,
)


logger = logging.getLogger(__name__)


def register_monster_command(command_tree: app_commands.CommandTree) -> None:
    """Register the /몬스터 command."""

    @command_tree.command(name=MONSTER_COMMAND.name, description=MONSTER_COMMAND.description)
    @app_commands.rename(name="이름")
    @app_commands.describe(name="검색할 몬스터 이름")
    async def monster(interaction: discord.Interaction, name: str) -> None:
        logger.info("/몬스터 command executed.")
        try:
            await interaction.response.defer(thinking=True)
            response = await get_monster_search_response(name)
            if response.embed:
                await interaction.followup.send(
                    content=response.content,
                    embed=_create_monster_embed(response.embed),
                )
                return

            await interaction.followup.send(response.content)
        except discord.HTTPException:
            logger.error("Failed to send /몬스터 response.", exc_info=True)
            raise
        except Exception:
            logger.error("/몬스터 command failed.", exc_info=True)
            raise

    @command_tree.command(
        name=MONSTER_DROP_COMMAND.name,
        description=MONSTER_DROP_COMMAND.description,
    )
    @app_commands.rename(name="이름")
    @app_commands.describe(name="드랍 정보를 검색할 몬스터 이름")
    async def monster_drop(interaction: discord.Interaction, name: str) -> None:
        logger.info("/몬스터드랍 command executed.")
        try:
            await interaction.response.defer(thinking=True)
            response = await get_monster_drop_search_response(name)
            if response.drop_items:
                await send_monster_drop_result(
                    interaction,
                    response.drop_items,
                    content=response.content,
                    monster_detail_url=response.monster_detail_url or "",
                )
                return

            if response.embeds:
                await interaction.followup.send(
                    content=response.content,
                    embeds=[
                        _create_monster_embed(embed_data)
                        for embed_data in response.embeds
                    ],
                )
                return

            await interaction.followup.send(response.content)
        except discord.HTTPException:
            logger.error("Failed to send /몬스터드랍 response.", exc_info=True)
            raise
        except Exception:
            logger.error("/몬스터드랍 command failed.", exc_info=True)
            raise


def build_drop_item_embeds(
    drops_slice: list[MonsterDropItem],
    monster_detail_url: str = "",
) -> list[MonsterEmbedData]:
    """Build embeds for the visible drop slice only."""
    return [
        MonsterEmbedData(
            title=drop_item.name,
            description=f"드랍률: {drop_item.drop_rate or '정보 없음'}",
            url=drop_item.detail_url or monster_detail_url,
            thumbnail_url=drop_item.icon_url,
            fields=[],
            footer="",
        )
        for drop_item in drops_slice
    ]


def chunk_drops(
    drops: list[MonsterDropItem],
    size: int = DEFAULT_MONSTER_DROP_PAGE_SIZE,
) -> list[list[MonsterDropItem]]:
    return [drops[index : index + size] for index in range(0, len(drops), size)]


def build_pagination_row(
    current_page: int,
    total_pages: int,
    token: str,
) -> list[discord.ui.Button]:
    previous_button = discord.ui.Button(
        label="◀ 이전",
        style=discord.ButtonStyle.secondary,
        custom_id=f"monsterdrop_prev_{token}",
        disabled=current_page == 0,
    )
    page_button = discord.ui.Button(
        label=f"{current_page + 1} / {total_pages}",
        style=discord.ButtonStyle.secondary,
        custom_id=f"monsterdrop_page_{token}",
        disabled=True,
    )
    next_button = discord.ui.Button(
        label="다음 ▶",
        style=discord.ButtonStyle.secondary,
        custom_id=f"monsterdrop_next_{token}",
        disabled=current_page >= total_pages - 1,
    )
    return [previous_button, page_button, next_button]


def disable_pagination_row(row: list[discord.ui.Button]) -> list[discord.ui.Button]:
    for button in row:
        button.disabled = True
    return row


def build_expired_pagination_notice() -> discord.ui.Button:
    return discord.ui.Button(
        label="조회 가능 시간이 끝났어요. 다시 조회해 주세요.",
        emoji="⚠️",
        style=discord.ButtonStyle.danger,
        disabled=True,
        row=1,
    )


async def send_monster_drop_result(
    interaction: discord.Interaction,
    drops: list[MonsterDropItem],
    content: str | None = None,
    monster_detail_url: str = "",
) -> None:
    view = MonsterDropPaginationView(
        drops=drops,
        monster_detail_url=monster_detail_url,
        content=content,
    )
    has_multiple_pages = view.total_pages > 1
    message = await interaction.followup.send(
        content=view.active_content if has_multiple_pages else content,
        embeds=view.current_embeds,
        view=view if has_multiple_pages else None,
        wait=True,
    )
    if has_multiple_pages:
        view.message = message


class MonsterDropPaginationView(discord.ui.View):
    """Per-message pagination state for monster drop embeds."""

    def __init__(
        self,
        drops: list[MonsterDropItem],
        monster_detail_url: str,
        content: str | None = None,
        page_size: int = DEFAULT_MONSTER_DROP_PAGE_SIZE,
        token: str | None = None,
    ) -> None:
        super().__init__(timeout=DEFAULT_MONSTER_DROP_PAGINATION_TIMEOUT_SECONDS)
        self.drops = drops
        self.monster_detail_url = monster_detail_url
        self.content = content
        self.page_size = page_size
        self.current_page = 0
        self.token = token or secrets.token_hex(8)
        self.message: discord.Message | None = None
        self.total_pages = max(1, math.ceil(len(drops) / page_size))
        self._refresh_buttons()

    @property
    def active_content(self) -> str | None:
        if not self.content:
            return "조회 가능 시간: 3분"
        return f"{self.content}\n조회 가능 시간: 3분"

    @property
    def expired_content(self) -> str | None:
        return self.content

    def _mark_expired(self) -> None:
        disable_pagination_row(list(self.children))
        self.add_item(build_expired_pagination_notice())


    @property
    def current_embeds(self) -> list[discord.Embed]:
        start = self.current_page * self.page_size
        end = start + self.page_size
        embed_data_list = build_drop_item_embeds(
            self.drops[start:end],
            monster_detail_url=self.monster_detail_url,
        )
        return [_create_monster_embed(embed_data) for embed_data in embed_data_list]

    def _refresh_buttons(self) -> None:
        self.clear_items()
        for button in build_pagination_row(
            self.current_page,
            self.total_pages,
            self.token,
        ):
            if button.custom_id == f"monsterdrop_prev_{self.token}":
                button.callback = self._go_previous
            elif button.custom_id == f"monsterdrop_next_{self.token}":
                button.callback = self._go_next
            self.add_item(button)

    async def _go_previous(self, interaction: discord.Interaction) -> None:
        self.current_page = max(0, self.current_page - 1)
        await self._update_message(interaction)

    async def _go_next(self, interaction: discord.Interaction) -> None:
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self._update_message(interaction)

    async def _update_message(self, interaction: discord.Interaction) -> None:
        self._refresh_buttons()
        try:
            await interaction.response.edit_message(embeds=self.current_embeds, view=self)
        except discord.HTTPException:
            logger.error("Failed to handle monster drop pagination button.", exc_info=True)
            raise
        except Exception:
            logger.error("Monster drop pagination button failed.", exc_info=True)
            raise

    async def on_timeout(self) -> None:
        self._mark_expired()
        try:
            if self.message:
                await self.message.edit(content=self.expired_content, view=self)
        except discord.NotFound:
            pass
        except discord.HTTPException:
            logger.error("Failed to update expired monster drop pagination.", exc_info=True)
        finally:
            self.drops = []


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
