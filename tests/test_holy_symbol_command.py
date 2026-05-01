import asyncio

from app.bot.holy_symbol import register_holy_symbol_commands
from app.bot.holy_symbol_command_config import (
    HOLY_SYMBOL_START_COMMAND,
    HOLY_SYMBOL_STATUS_COMMAND,
    HOLY_SYMBOL_STOP_COMMAND,
)
from app.services.holy_symbol_timer_service import HolySymbolTimerService


class FakeResponse:
    def __init__(self) -> None:
        self.message: str | None = None
        self.ephemeral: bool | None = None

    async def send_message(self, message: str, **kwargs) -> None:
        self.message = message
        self.ephemeral = kwargs.get("ephemeral")


class FakeUser:
    id = 10


class FakeChannel:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send(self, message: str) -> None:
        self.messages.append(message)


class FakeInteraction:
    def __init__(self) -> None:
        self.response = FakeResponse()
        self.user = FakeUser()
        self.guild_id = 1
        self.channel = FakeChannel()


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


def test_register_holy_symbol_commands_registers_commands() -> None:
    command_tree = FakeCommandTree()
    service = HolySymbolTimerService()

    register_holy_symbol_commands(command_tree, service)

    assert HOLY_SYMBOL_START_COMMAND.name in command_tree.commands
    assert HOLY_SYMBOL_STOP_COMMAND.name in command_tree.commands
    assert HOLY_SYMBOL_STATUS_COMMAND.name in command_tree.commands


def test_holy_symbol_start_command_starts_timer_with_ephemeral_response() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)

        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "홀심 타이머를 시작했습니다."
        assert interaction.response.ephemeral is True
        assert service.get_holy_symbol_remaining_seconds(1, 10) is not None
        service.cancel_all()

    asyncio.run(run_test())


def test_holy_symbol_stop_command_stops_timer_with_ephemeral_response() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)
        service.start_holy_symbol_timer(1, 10, interaction.channel)

        await command_tree.commands[HOLY_SYMBOL_STOP_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "홀심 타이머를 중지했습니다."
        assert interaction.response.ephemeral is True
        assert service.get_holy_symbol_remaining_seconds(1, 10) is None

    asyncio.run(run_test())


def test_holy_symbol_stop_command_handles_missing_timer() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)

        await command_tree.commands[HOLY_SYMBOL_STOP_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "실행 중인 홀심 타이머가 없습니다."
        assert interaction.response.ephemeral is True

    asyncio.run(run_test())


def test_holy_symbol_status_command_returns_remaining_time() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)
        service.start_holy_symbol_timer(1, 10, interaction.channel)

        await command_tree.commands[HOLY_SYMBOL_STATUS_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "홀심 남은 시간: 2분 0초"
        assert interaction.response.ephemeral is True
        service.cancel_all()

    asyncio.run(run_test())


def test_holy_symbol_status_command_handles_missing_timer() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)

        await command_tree.commands[HOLY_SYMBOL_STATUS_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "실행 중인 홀심 타이머가 없습니다."
        assert interaction.response.ephemeral is True

    asyncio.run(run_test())
