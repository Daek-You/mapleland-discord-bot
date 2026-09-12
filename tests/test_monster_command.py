import asyncio
import logging

import discord
import pytest

import app.bot.monster as monster_command
from app.bot.command_config import MONSTER_COMMAND, MONSTER_DROP_COMMAND
from app.bot.monster import register_monster_command
from app.crawler.maplenote import MonsterDropItem
from app.services.monster_service import (
    MonsterEmbedData,
    MonsterEmbedField,
    MonsterSearchResponse,
)


class FakeResponse:
    def __init__(self) -> None:
        self.message: str | None = None
        self.embed = None
        self.embeds = None
        self.view = None
        self.edited_embeds = None
        self.edited_view = None
        self.deferred = False

    async def defer(self, *, thinking: bool = False) -> None:
        self.deferred = thinking

    async def send_message(self, message: str | None = None, **kwargs) -> None:
        self.message = message or kwargs.get("content")
        self.embed = kwargs.get("embed")
        self.embeds = kwargs.get("embeds")
        self.view = kwargs.get("view")

    async def edit_message(self, **kwargs) -> None:
        self.edited_embeds = kwargs.get("embeds")
        self.edited_view = kwargs.get("view")


class FakeMessage:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.edited_content = None
        self.edited_view = None

    async def edit(self, **kwargs) -> None:
        self.edited_content = kwargs.get("content")
        self.edited_view = kwargs.get("view")


class FakeFollowup:
    def __init__(self, sent_message: FakeMessage) -> None:
        self.message: str | None = None
        self.embed = None
        self.embeds = None
        self.view = None
        self.sent_message = sent_message

    async def send(self, message: str | None = None, **kwargs) -> FakeMessage:
        self.message = message or kwargs.get("content")
        self.embed = kwargs.get("embed")
        self.embeds = kwargs.get("embeds")
        self.view = kwargs.get("view")
        return self.sent_message


class FakeInteraction:
    def __init__(self) -> None:
        self.response = FakeResponse()
        self.message = FakeMessage(self.response)
        self.followup = FakeFollowup(self.message)

    async def original_response(self) -> FakeMessage:
        return self.message


class FakeCommandTree:
    def __init__(self) -> None:
        self.commands = {}

    def command(self, name: str, description: str):
        def decorator(callback):
            self.commands[name] = {
                "callback": callback,
                "description": description,
            }
            return callback

        return decorator


def make_async_response(factory):
    async def get_response(name: str) -> MonsterSearchResponse:
        return factory(name)

    return get_response


def test_register_monster_command_registers_command() -> None:
    command_tree = FakeCommandTree()

    register_monster_command(command_tree)

    assert MONSTER_COMMAND.name in command_tree.commands
    assert command_tree.commands[MONSTER_COMMAND.name]["description"] == MONSTER_COMMAND.description
    assert MONSTER_DROP_COMMAND.name in command_tree.commands
    assert (
        command_tree.commands[MONSTER_DROP_COMMAND.name]["description"]
        == MONSTER_DROP_COMMAND.description
    )


def test_monster_command_sends_search_message(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        monster_command,
        "get_monster_search_response",
        make_async_response(
            lambda name: MonsterSearchResponse(content=f"{name} 검색 결과")
        ),
    )

    register_monster_command(command_tree)
    asyncio.run(command_tree.commands[MONSTER_COMMAND.name]["callback"](interaction, "슬라임"))

    assert interaction.response.deferred is True
    assert interaction.followup.message == "슬라임 검색 결과"
    assert interaction.followup.embed is None


def test_monster_command_sends_embed_response(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        monster_command,
        "get_monster_search_response",
        make_async_response(
            lambda name: MonsterSearchResponse(
                embed=MonsterEmbedData(
                    title="슬라임",
                    description="몬스터 정보",
                    url="https://example.com/monster_card/210100",
                    thumbnail_url="https://example.com/slime.png",
                    fields=[
                        MonsterEmbedField(name="기본 정보", value="LV: 6", inline=True),
                    ],
                    footer="메이플노트 클래식",
                ),
            )
        ),
    )

    register_monster_command(command_tree)
    asyncio.run(command_tree.commands[MONSTER_COMMAND.name]["callback"](interaction, "슬라임"))

    assert interaction.response.deferred is True
    assert interaction.followup.message is None
    assert interaction.followup.embed.title == "슬라임"
    assert interaction.followup.embed.url == "https://example.com/monster_card/210100"
    assert interaction.followup.embeds is None


def test_monster_drop_command_sends_drop_embeds(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        monster_command,
        "get_monster_drop_search_response",
        make_async_response(
            lambda name: MonsterSearchResponse(
                content=f"**{name} 주요 드랍 아이템**",
                embeds=[
                    MonsterEmbedData(
                        title="물컹물컹한 액체",
                        description="드랍률: 40%",
                        url="https://example.com/item_detail/4000004",
                        thumbnail_url="https://example.com/item.png",
                        fields=[],
                        footer="",
                    )
                ],
            )
        ),
    )

    register_monster_command(command_tree)
    asyncio.run(
        command_tree.commands[MONSTER_DROP_COMMAND.name]["callback"](interaction, "슬라임")
    )

    assert interaction.followup.message == "**슬라임 주요 드랍 아이템**"
    assert interaction.followup.embeds[0].title == "물컹물컹한 액체"


def test_monster_drop_command_paginates_drop_embeds(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        monster_command,
        "get_monster_drop_search_response",
        make_async_response(
            lambda name: MonsterSearchResponse(
                content=f"**{name} 주요 드랍 아이템**",
                drop_items=[
                    MonsterDropItem(
                        name=f"아이템 {index}",
                        drop_rate=f"{index}%",
                        icon_url=f"https://example.com/item/{index}.png",
                    )
                    for index in range(1, 10)
                ],
                monster_detail_url="https://example.com/monster_card/210100",
            )
        ),
    )

    register_monster_command(command_tree)
    asyncio.run(
        command_tree.commands[MONSTER_DROP_COMMAND.name]["callback"](interaction, "슬라임")
    )

    assert interaction.followup.message == "**슬라임 주요 드랍 아이템**\n조회 가능 시간: 3분"
    assert len(interaction.followup.embeds) == 7
    assert interaction.followup.embeds[0].title == "아이템 1"
    assert interaction.followup.embeds[-1].title == "아이템 7"
    assert interaction.followup.view is not None
    assert interaction.followup.view.total_pages == 2
    assert interaction.followup.view.children[0].disabled is True
    assert interaction.followup.view.children[1].label == "1 / 2"
    assert interaction.followup.view.children[2].disabled is False


def test_monster_drop_pagination_next_button_updates_message() -> None:
    interaction = FakeInteraction()
    view = monster_command.MonsterDropPaginationView(
        drops=[
            MonsterDropItem(name=f"아이템 {index}", drop_rate=f"{index}%")
            for index in range(1, 10)
        ],
        monster_detail_url="https://example.com/monster_card/210100",
    )

    asyncio.run(view.children[2].callback(interaction))

    assert interaction.response.edited_embeds[0].title == "아이템 8"
    assert interaction.response.edited_view.children[0].disabled is False
    assert interaction.response.edited_view.children[1].label == "2 / 2"
    assert interaction.response.edited_view.children[2].disabled is True


def test_monster_drop_pagination_button_logs_http_failure(caplog) -> None:
    class FakeDiscordResponse:
        status = 500
        reason = "Server Error"

    class FailedResponse:
        async def edit_message(self, **kwargs) -> None:
            raise discord.HTTPException(
                response=FakeDiscordResponse(),
                message="edit failed",
            )

    class FailedInteraction:
        response = FailedResponse()

    view = monster_command.MonsterDropPaginationView(
        drops=[
            MonsterDropItem(name=f"아이템 {index}", drop_rate=f"{index}%")
            for index in range(1, 10)
        ],
        monster_detail_url="https://example.com/monster_card/210100",
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(discord.HTTPException):
            asyncio.run(view.children[2].callback(FailedInteraction()))

    assert "Failed to handle monster drop pagination button." in caplog.text
    assert "discord.errors.HTTPException" in caplog.text


def test_monster_drop_pagination_timeout_disables_buttons_and_clears_drops() -> None:
    interaction = FakeInteraction()
    view = monster_command.MonsterDropPaginationView(
        drops=[
            MonsterDropItem(name=f"아이템 {index}", drop_rate=f"{index}%")
            for index in range(1, 10)
        ],
        monster_detail_url="https://example.com/monster_card/210100",
        content="**슬라임 주요 드랍 아이템**",
    )
    view.message = interaction.message

    asyncio.run(view.on_timeout())

    assert all(child.disabled for child in view.children)
    assert view.drops == []
    assert interaction.message.edited_content == "**슬라임 주요 드랍 아이템**"
    assert interaction.message.edited_view is view
    assert len(interaction.message.edited_view.children) == 4
    expired_notice = interaction.message.edited_view.children[3]
    assert expired_notice.label == "조회 가능 시간이 끝났어요. 다시 조회해 주세요."
    assert expired_notice.emoji.name == "⚠️"
    assert expired_notice.style is discord.ButtonStyle.danger
    assert expired_notice.disabled is True
    assert expired_notice.row == 1


def test_monster_drop_pagination_timeout_ignores_deleted_message() -> None:
    class FakeDiscordResponse:
        status = 404
        reason = "Not Found"

    class DeletedMessage:
        async def edit(self, **kwargs) -> None:
            raise discord.NotFound(
                response=FakeDiscordResponse(),
                message={"code": 10008, "message": "Unknown Message"},
            )

    view = monster_command.MonsterDropPaginationView(
        drops=[
            MonsterDropItem(name=f"아이템 {index}", drop_rate=f"{index}%")
            for index in range(1, 10)
        ],
        monster_detail_url="https://example.com/monster_card/210100",
        content="**슬라임 주요 드랍 아이템**",
    )
    view.message = DeletedMessage()

    asyncio.run(view.on_timeout())

    assert all(child.disabled for child in view.children)
    assert view.drops == []


def test_monster_drop_command_omits_buttons_for_single_page(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        monster_command,
        "get_monster_drop_search_response",
        make_async_response(
            lambda name: MonsterSearchResponse(
                content=f"**{name} 주요 드랍 아이템**",
                drop_items=[MonsterDropItem(name="물컹물컹한 액체", drop_rate="")],
                monster_detail_url="https://example.com/monster_card/210100",
            )
        ),
    )

    register_monster_command(command_tree)
    asyncio.run(
        command_tree.commands[MONSTER_DROP_COMMAND.name]["callback"](interaction, "슬라임")
    )

    assert len(interaction.followup.embeds) == 1
    assert interaction.followup.embeds[0].description == "드랍률: 정보 없음"
    assert interaction.followup.view is None
