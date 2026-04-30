import asyncio

import app.bot.monster as monster_command
from app.bot.command_config import MONSTER_COMMAND, MONSTER_DROP_COMMAND
from app.bot.monster import register_monster_command
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

    async def send_message(self, message: str | None = None, **kwargs) -> None:
        self.message = message or kwargs.get("content")
        self.embed = kwargs.get("embed")
        self.embeds = kwargs.get("embeds")


class FakeFollowup:
    def __init__(self) -> None:
        self.embeds = None

    async def send(self, **kwargs) -> None:
        self.embeds = kwargs.get("embeds")


class FakeInteraction:
    def __init__(self) -> None:
        self.response = FakeResponse()
        self.followup = FakeFollowup()


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
        lambda name: MonsterSearchResponse(content=f"{name} 검색 결과"),
    )

    register_monster_command(command_tree)
    asyncio.run(command_tree.commands[MONSTER_COMMAND.name]["callback"](interaction, "슬라임"))

    assert interaction.response.message == "슬라임 검색 결과"
    assert interaction.response.embed is None


def test_monster_command_sends_embed_response(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        monster_command,
        "get_monster_search_response",
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
        ),
    )

    register_monster_command(command_tree)
    asyncio.run(command_tree.commands[MONSTER_COMMAND.name]["callback"](interaction, "슬라임"))

    assert interaction.response.message is None
    assert interaction.response.embed.title == "슬라임"
    assert interaction.response.embed.url == "https://example.com/monster_card/210100"
    assert interaction.followup.embeds is None


def test_monster_drop_command_sends_drop_embeds(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        monster_command,
        "get_monster_drop_search_response",
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
        ),
    )

    register_monster_command(command_tree)
    asyncio.run(
        command_tree.commands[MONSTER_DROP_COMMAND.name]["callback"](interaction, "슬라임")
    )

    assert interaction.response.message == "**슬라임 주요 드랍 아이템**"
    assert interaction.response.embeds[0].title == "물컹물컹한 액체"
