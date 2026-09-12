import asyncio

import app.bot.notice as notice_command
from app.bot.command_config import NOTICE_COMMAND
from app.bot.notice import register_notice_command


class FakeResponse:
    def __init__(self) -> None:
        self.deferred = False

    async def defer(self, *, thinking: bool = False) -> None:
        self.deferred = thinking


class FakeFollowup:
    def __init__(self) -> None:
        self.message: str | None = None

    async def send(self, message: str) -> None:
        self.message = message


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


def test_register_notice_command_registers_notice() -> None:
    command_tree = FakeCommandTree()

    register_notice_command(command_tree)

    assert NOTICE_COMMAND.name in command_tree.commands
    assert command_tree.commands[NOTICE_COMMAND.name]["description"] == NOTICE_COMMAND.description


def test_notice_command_sends_latest_notice_message(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()

    async def get_latest_notice_message(**kwargs) -> str:
        return "공지 응답"

    monkeypatch.setattr(notice_command, "get_latest_notice_message", get_latest_notice_message)

    register_notice_command(command_tree)
    asyncio.run(command_tree.commands[NOTICE_COMMAND.name]["callback"](interaction))

    assert interaction.response.deferred is True
    assert interaction.followup.message == "공지 응답"


def test_notice_command_uses_injected_fetcher() -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()

    async def fetch_notice_items():
        return []

    register_notice_command(
        command_tree,
        fetch_notice_items=fetch_notice_items,
    )
    asyncio.run(command_tree.commands[NOTICE_COMMAND.name]["callback"](interaction))

    assert interaction.followup.message == "현재 가져올 수 있는 공지가 없습니다."
