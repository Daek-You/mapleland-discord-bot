import asyncio

import discord

from app.bot.holy_symbol import ThreadNotifier, register_holy_symbol_commands
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
    def __init__(self, user_id: int = 10, display_name: str = "테스터") -> None:
        self.id = user_id
        self.display_name = display_name
        self.name = display_name


class FakeThread:
    def __init__(self, thread_id: int, name: str) -> None:
        self.id = thread_id
        self.name = name
        self.messages: list[str] = []
        self.added_users: list[FakeUser] = []
        self.deleted = False

    async def add_user(self, user: FakeUser) -> None:
        self.added_users.append(user)

    async def send(self, message: str) -> None:
        self.messages.append(message)

    async def delete(self) -> None:
        self.deleted = True


class FakeChannel:
    def __init__(self) -> None:
        self.next_thread_id = 1000
        self.threads: list[FakeThread] = []

    async def create_thread(self, **kwargs) -> FakeThread:
        thread = FakeThread(self.next_thread_id, kwargs["name"])
        self.next_thread_id += 1
        self.threads.append(thread)
        return thread


class FakeClient:
    def __init__(self) -> None:
        self.channels: dict[int, object] = {}

    def get_channel(self, channel_id: int) -> object | None:
        return self.channels.get(channel_id)

    async def fetch_channel(self, channel_id: int) -> object | None:
        return self.channels.get(channel_id)


class FakeInteraction:
    def __init__(self, user_id: int = 10, display_name: str = "테스터") -> None:
        self.response = FakeResponse()
        self.user = FakeUser(user_id, display_name)
        self.guild_id = 1
        self.guild = None
        self.channel = FakeChannel()
        self.client = FakeClient()


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
        register_holy_symbol_commands(
            command_tree,
            service,
            thread_delete_delay_seconds=0,
        )

        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "홀심 타이머를 시작했습니다."
        assert interaction.response.ephemeral is True
        assert service.get_holy_symbol_remaining_seconds(1, 10) is not None
        assert len(interaction.channel.threads) == 1
        thread = interaction.channel.threads[0]
        assert thread.name == "테스터-홀심"
        assert thread.added_users == [interaction.user]
        assert thread.messages == ["홀심 타이머 시작 (100초)"]
        service.cancel_all()

    asyncio.run(run_test())


def test_holy_symbol_stop_command_stops_timer_with_ephemeral_response() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(
            command_tree,
            service,
            thread_delete_delay_seconds=0,
        )
        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            interaction
        )

        await command_tree.commands[HOLY_SYMBOL_STOP_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "홀심 타이머를 중지했습니다."
        assert interaction.response.ephemeral is True
        assert service.get_holy_symbol_remaining_seconds(1, 10) is None
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert (
            interaction.channel.threads[0].messages[-1]
            == "타이머를 중지했습니다.\n이 스레드는 곧 삭제됩니다."
        )
        assert interaction.channel.threads[0].deleted is True

    asyncio.run(run_test())


def test_thread_notifier_ignores_already_deleted_thread() -> None:
    class FakeResponseForNotFound:
        status = 404
        reason = "Not Found"

    class DeletedThread(FakeThread):
        async def delete(self) -> None:
            raise discord.NotFound(FakeResponseForNotFound(), "missing")

    async def run_test() -> None:
        thread = DeletedThread(1000, "deleted")
        notifier = ThreadNotifier(thread, delete_delay_seconds=0)

        await notifier.close("타이머 종료됨")
        await asyncio.sleep(0)

        assert thread.messages == ["타이머 종료됨\n이 스레드는 곧 삭제됩니다."]

    asyncio.run(run_test())


def test_thread_notifier_logs_discord_delete_failure() -> None:
    class FakeResponseForHttpException:
        status = 500
        reason = "Server Error"

    class FailingThread(FakeThread):
        async def delete(self) -> None:
            raise discord.HTTPException(FakeResponseForHttpException(), "failed")

    async def run_test() -> None:
        thread = FailingThread(1000, "failing")
        notifier = ThreadNotifier(thread, delete_delay_seconds=0)

        await notifier.close("타이머 종료됨")
        await asyncio.sleep(0)

        assert thread.messages == ["타이머 종료됨\n이 스레드는 곧 삭제됩니다."]

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
        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            interaction
        )

        await command_tree.commands[HOLY_SYMBOL_STATUS_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "홀심 남은 시간: 1분 40초"
        assert interaction.response.ephemeral is True
        service.cancel_all()

    asyncio.run(run_test())


def test_holy_symbol_start_command_reuses_existing_thread() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)

        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            interaction
        )
        first_thread = interaction.channel.threads[0]
        interaction.client.channels[first_thread.id] = first_thread

        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "기존 홀심 타이머를 재시작했습니다."
        assert len(interaction.channel.threads) == 1
        assert service.get_holy_symbol_timer(1, 10).thread_id == first_thread.id
        assert first_thread.messages == [
            "홀심 타이머 시작 (100초)",
            "홀심 타이머 시작 (100초)",
        ]
        service.cancel_all()

    asyncio.run(run_test())


def test_holy_symbol_start_command_keeps_different_users_independent() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        first_interaction = FakeInteraction(10, "첫번째")
        second_interaction = FakeInteraction(20, "두번째")
        second_interaction.channel = first_interaction.channel
        second_interaction.client = first_interaction.client
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)

        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            first_interaction
        )
        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            second_interaction
        )

        assert service.get_holy_symbol_timer(1, 10).thread_id == 1000
        assert service.get_holy_symbol_timer(1, 20).thread_id == 1001
        assert first_interaction.channel.threads[0].name == "첫번째-홀심"
        assert first_interaction.channel.threads[1].name == "두번째-홀심"
        service.cancel_all()

    asyncio.run(run_test())


def test_holy_symbol_start_command_creates_new_thread_when_existing_is_missing() -> None:
    async def run_test() -> None:
        command_tree = FakeCommandTree()
        interaction = FakeInteraction()
        service = HolySymbolTimerService()
        register_holy_symbol_commands(command_tree, service)
        service.start_holy_symbol_timer(1, 10, 9999, FakeThread(9999, "deleted"))

        await command_tree.commands[HOLY_SYMBOL_START_COMMAND.name]["callback"](
            interaction
        )

        assert interaction.response.message == "기존 홀심 타이머를 재시작했습니다."
        assert len(interaction.channel.threads) == 1
        assert service.get_holy_symbol_timer(1, 10).thread_id == 1000
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
