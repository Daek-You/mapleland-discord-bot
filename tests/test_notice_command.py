import asyncio

import app.bot.notice as notice_command
from app.bot.notice import register_notice_command


class FakeResponse:
    def __init__(self) -> None:
        self.message: str | None = None

    async def send_message(self, message: str) -> None:
        self.message = message


class FakeInteraction:
    def __init__(self) -> None:
        self.response = FakeResponse()


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

    assert "공지" in command_tree.commands
    assert command_tree.commands["공지"]["description"]


def test_notice_command_sends_latest_notice_message(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(notice_command, "get_latest_notice_message", lambda: "공지 응답")

    register_notice_command(command_tree)
    asyncio.run(command_tree.commands["공지"]["callback"](interaction))

    assert interaction.response.message == "공지 응답"
