import asyncio

from app.services.holy_symbol_timer_service import (
    HolySymbolTimerService,
    format_holy_symbol_expired_message,
    format_holy_symbol_start_response,
    format_holy_symbol_status_response,
    format_holy_symbol_stop_response,
    format_holy_symbol_warning_message,
)


class ManualClock:
    def __init__(self) -> None:
        self.now = 100.0

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def current_time(self) -> float:
        return self.now


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send(self, message: str) -> None:
        self.messages.append(message)


async def immediate_sleep(seconds: float) -> None:
    await asyncio.sleep(0)


def test_start_holy_symbol_timer_creates_timer() -> None:
    async def run_test() -> None:
        clock = ManualClock()
        service = HolySymbolTimerService(now=clock.current_time)

        restarted = service.start_holy_symbol_timer(1, 10, FakeNotifier())

        assert restarted is False
        assert service.get_holy_symbol_remaining_seconds(1, 10) == 120
        service.cancel_all()

    asyncio.run(run_test())


def test_start_holy_symbol_timer_replaces_same_user_timer() -> None:
    async def run_test() -> None:
        clock = ManualClock()
        service = HolySymbolTimerService(now=clock.current_time)

        service.start_holy_symbol_timer(1, 10, FakeNotifier())
        clock.advance(30)
        restarted = service.start_holy_symbol_timer(1, 10, FakeNotifier())

        assert restarted is True
        assert service.get_holy_symbol_remaining_seconds(1, 10) == 120
        service.cancel_all()

    asyncio.run(run_test())


def test_different_users_keep_independent_timers() -> None:
    async def run_test() -> None:
        clock = ManualClock()
        service = HolySymbolTimerService(now=clock.current_time)

        service.start_holy_symbol_timer(1, 10, FakeNotifier())
        clock.advance(30)
        service.start_holy_symbol_timer(1, 20, FakeNotifier())

        assert service.get_holy_symbol_remaining_seconds(1, 10) == 90
        assert service.get_holy_symbol_remaining_seconds(1, 20) == 120
        service.cancel_all()

    asyncio.run(run_test())


def test_stop_holy_symbol_timer_removes_only_matching_user_timer() -> None:
    async def run_test() -> None:
        service = HolySymbolTimerService()
        service.start_holy_symbol_timer(1, 10, FakeNotifier())
        service.start_holy_symbol_timer(1, 20, FakeNotifier())

        stopped = service.stop_holy_symbol_timer(1, 10)

        assert stopped is True
        assert service.get_holy_symbol_remaining_seconds(1, 10) is None
        assert service.get_holy_symbol_remaining_seconds(1, 20) is not None
        service.cancel_all()

    asyncio.run(run_test())


def test_status_returns_remaining_seconds() -> None:
    async def run_test() -> None:
        clock = ManualClock()
        service = HolySymbolTimerService(now=clock.current_time)
        service.start_holy_symbol_timer(1, 10, FakeNotifier())

        clock.advance(78)

        assert service.get_holy_symbol_remaining_seconds(1, 10) == 42
        service.cancel_all()

    asyncio.run(run_test())


def test_missing_timer_returns_none_and_empty_state_message() -> None:
    service = HolySymbolTimerService()

    assert service.get_holy_symbol_remaining_seconds(1, 10) is None
    assert service.stop_holy_symbol_timer(1, 10) is False
    assert format_holy_symbol_status_response(None) == "실행 중인 홀심 타이머가 없습니다."
    assert format_holy_symbol_stop_response(False) == "실행 중인 홀심 타이머가 없습니다."


def test_holy_symbol_response_formatters() -> None:
    assert format_holy_symbol_start_response(False) == "홀심 타이머를 시작했습니다."
    assert format_holy_symbol_start_response(True) == "기존 홀심 타이머를 재시작했습니다."
    assert format_holy_symbol_stop_response(True) == "홀심 타이머를 중지했습니다."
    assert format_holy_symbol_status_response(42) == "홀심 남은 시간: 42초"
    assert format_holy_symbol_warning_message(10) == "<@10> 🔔 홀심 10초 남음"
    assert format_holy_symbol_expired_message(10) == "<@10> ✨ 홀심 다시 사용!"


def test_timer_sends_warning_and_expiration_notifications() -> None:
    async def run_test() -> None:
        notifier = FakeNotifier()
        service = HolySymbolTimerService(sleep=immediate_sleep)

        service.start_holy_symbol_timer(1, 10, notifier)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert notifier.messages == [
            "<@10> 🔔 홀심 10초 남음",
            "<@10> ✨ 홀심 다시 사용!",
        ]

    asyncio.run(run_test())
