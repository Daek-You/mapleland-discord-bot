import asyncio

from app.bot.ping import register_ping_command


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


def test_register_ping_command_registers_ping() -> None:
    command_tree = FakeCommandTree()

    register_ping_command(command_tree)

    assert "ping" in command_tree.commands
    assert command_tree.commands["ping"]["description"]


def test_ping_command_sends_pong() -> None:
    command_tree = FakeCommandTree()
    interaction = FakeInteraction()
    register_ping_command(command_tree)

    asyncio.run(command_tree.commands["ping"]["callback"](interaction))

    assert interaction.response.message == "Pong!"
