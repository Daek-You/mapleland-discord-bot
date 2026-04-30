import asyncio

import app.bot.notification_test as notification_test_command
from app.bot.command_config import NOTIFICATION_TEST_COMMAND
from app.bot.notification_test import register_notification_test_command
from app.services.notification_service import NoticeNotification


class FakeResponse:
    def __init__(self) -> None:
        self.message: str | None = None

    async def send_message(self, message: str) -> None:
        self.message = message


class FakeInteraction:
    id = 12345

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


def test_register_notification_test_command_registers_command() -> None:
    command_tree = FakeCommandTree()

    register_notification_test_command(command_tree)

    assert NOTIFICATION_TEST_COMMAND.name in command_tree.commands
    assert (
        command_tree.commands[NOTIFICATION_TEST_COMMAND.name]["description"]
        == NOTIFICATION_TEST_COMMAND.description
    )


def test_notification_test_command_sends_fake_notice(monkeypatch) -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    monkeypatch.setattr(
        notification_test_command,
        "collect_test_notice_notifications",
        lambda unique_suffix: [
            NoticeNotification(
                title="Fake notice",
                url=f"https://example.com/{unique_suffix}",
            )
        ],
    )

    register_notification_test_command(command_tree)
    asyncio.run(
        command_tree.commands[NOTIFICATION_TEST_COMMAND.name]["callback"](interaction)
    )

    assert interaction.response.message == "Fake notice\nhttps://example.com/12345"
