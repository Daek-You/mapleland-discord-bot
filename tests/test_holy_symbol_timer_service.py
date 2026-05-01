import asyncio

from app.services.holy_symbol_timer_service import (
    HolySymbolTimerService,
    format_holy_symbol_expired_message,
    format_holy_symbol_expired_tts_message,
    format_remaining_time,
    format_holy_symbol_start_response,
    format_holy_symbol_status_response,
    format_holy_symbol_stop_response,
    format_holy_symbol_thread_close_message,
    format_holy_symbol_thread_delete_notice,
    format_holy_symbol_thread_finished_message,
    format_holy_symbol_thread_start_message,
    format_holy_symbol_thread_stop_message,
    format_holy_symbol_thread_unavailable_response,
    format_holy_symbol_tts_notice,
    format_holy_symbol_warning_message,
    format_holy_symbol_warning_tts_message,
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
        self.tts_messages: list[str] = []
        self.closed_messages: list[str] = []

    async def send(self, message: str) -> None:
        self.messages.append(message)

    async def send_tts(self, message: str) -> None:
        self.tts_messages.append(message)

    async def close(self, message: str) -> None:
        self.closed_messages.append(message)


def test_start_holy_symbol_timer_creates_timer() -> None:
    async def run_test() -> None:
        clock = ManualClock()
        service = HolySymbolTimerService(now=clock.current_time)

        restarted = service.start_holy_symbol_timer(1, 10, 1000, FakeNotifier())

        assert restarted is False
        assert service.get_holy_symbol_remaining_seconds(1, 10) == 100
        assert service.get_holy_symbol_timer(1, 10).thread_id == 1000
        service.cancel_all()

    asyncio.run(run_test())


def test_start_holy_symbol_timer_replaces_same_user_timer() -> None:
    async def run_test() -> None:
        clock = ManualClock()
        service = HolySymbolTimerService(now=clock.current_time)

        service.start_holy_symbol_timer(1, 10, 1000, FakeNotifier())
        clock.advance(30)
        restarted = service.start_holy_symbol_timer(1, 10, 1000, FakeNotifier())

        assert restarted is True
        assert service.get_holy_symbol_remaining_seconds(1, 10) == 100
        service.cancel_all()

    asyncio.run(run_test())


def test_different_users_keep_independent_timers() -> None:
    async def run_test() -> None:
        clock = ManualClock()
        service = HolySymbolTimerService(now=clock.current_time)

        service.start_holy_symbol_timer(1, 10, 1000, FakeNotifier())
        clock.advance(30)
        service.start_holy_symbol_timer(1, 20, 2000, FakeNotifier())

        assert service.get_holy_symbol_remaining_seconds(1, 10) == 70
        assert service.get_holy_symbol_remaining_seconds(1, 20) == 100
        assert service.get_holy_symbol_timer(1, 10).thread_id == 1000
        assert service.get_holy_symbol_timer(1, 20).thread_id == 2000
        service.cancel_all()

    asyncio.run(run_test())


def test_stop_holy_symbol_timer_removes_only_matching_user_timer() -> None:
    async def run_test() -> None:
        service = HolySymbolTimerService()
        service.start_holy_symbol_timer(1, 10, 1000, FakeNotifier())
        service.start_holy_symbol_timer(1, 20, 2000, FakeNotifier())

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
        service.start_holy_symbol_timer(1, 10, 1000, FakeNotifier())

        clock.advance(78)

        assert service.get_holy_symbol_remaining_seconds(1, 10) == 22
        service.cancel_all()

    asyncio.run(run_test())


def test_missing_timer_returns_none_and_empty_state_message() -> None:
    service = HolySymbolTimerService()

    assert service.get_holy_symbol_remaining_seconds(1, 10) is None
    assert service.stop_holy_symbol_timer(1, 10) is False
    assert format_holy_symbol_status_response(None) == "실행 중인 홀심 타이머가 없습니다."
    assert format_holy_symbol_stop_response(False) == "실행 중인 홀심 타이머가 없습니다."


def test_holy_symbol_response_formatters() -> None:
    assert (
        format_holy_symbol_start_response(False)
        == f"홀심 타이머를 시작했습니다.\n\n{format_holy_symbol_tts_notice()}"
    )
    assert (
        format_holy_symbol_start_response(True)
        == f"기존 홀심 타이머를 재시작했습니다.\n\n{format_holy_symbol_tts_notice()}"
    )
    assert format_holy_symbol_stop_response(True) == "홀심 타이머를 중지했습니다."
    assert format_holy_symbol_status_response(42) == "홀심 남은 시간: 42초"
    assert format_holy_symbol_status_response(72) == "홀심 남은 시간: 1분 12초"
    assert format_holy_symbol_thread_start_message(100) == "홀심 타이머 시작 (100초)"
    assert format_holy_symbol_thread_stop_message() == "타이머를 중지했습니다."
    assert format_holy_symbol_thread_finished_message() == "타이머 종료됨"
    assert format_holy_symbol_thread_delete_notice() == "이 스레드는 곧 삭제됩니다."
    assert (
        format_holy_symbol_thread_close_message("타이머 종료됨")
        == "타이머 종료됨\n이 스레드는 곧 삭제됩니다."
    )
    assert format_holy_symbol_warning_message() == "홀심 10초 남음"
    assert format_holy_symbol_warning_tts_message() == "홀심 10초 남음"
    assert format_holy_symbol_expired_message() == "홀심 다시 사용"
    assert format_holy_symbol_expired_tts_message() == "홀심 다시 사용"
    assert (
        format_holy_symbol_thread_unavailable_response()
        == "현재 채널에는 메랜도우미가 없어요. 메랜도우미가 있는 채널에서 다시 시도해주세요."
    )
    assert "켜지 않아도 됩니다" in format_holy_symbol_tts_notice()
    assert "타이머 스레드 채널을 보고 있어야 합니다" in format_holy_symbol_tts_notice()
    assert "텍스트 음성 변환(TTS) 속도" in format_holy_symbol_tts_notice()


def test_format_remaining_time_omits_minutes_when_under_one_minute() -> None:
    assert format_remaining_time(30) == "30초"
    assert format_remaining_time(60) == "1분 0초"
    assert format_remaining_time(125) == "2분 5초"


def test_timer_repeats_warning_and_expiration_notifications() -> None:
    async def run_test() -> None:
        sleep_count = 0

        async def repeat_sleep(seconds: float) -> None:
            nonlocal sleep_count
            sleep_count += 1
            if sleep_count > 4:
                raise asyncio.CancelledError
            await asyncio.sleep(0)

        notifier = FakeNotifier()
        service = HolySymbolTimerService(sleep=repeat_sleep)

        service.start_holy_symbol_timer(1, 10, 1000, notifier)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        assert notifier.messages == []
        assert notifier.tts_messages == [
            "홀심 10초 남음",
            "홀심 다시 사용",
            "홀심 10초 남음",
            "홀심 다시 사용",
        ]
        assert notifier.closed_messages == []

    asyncio.run(run_test())


def test_holy_symbol_timer_messages_do_not_include_decorative_characters() -> None:
    decorative_characters = ("🔔", "✨", "!", "→", "※")

    assert all(
        character not in format_holy_symbol_warning_tts_message()
        for character in decorative_characters
    )
    assert all(
        character not in format_holy_symbol_expired_tts_message()
        for character in decorative_characters
    )
    assert all(
        character not in format_holy_symbol_warning_message()
        for character in decorative_characters
    )
    assert all(
        character not in format_holy_symbol_expired_message()
        for character in decorative_characters
    )
