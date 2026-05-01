"""Service logic for Holy Symbol timer commands."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import math
import time
from typing import Protocol

from app.config import (
    DEFAULT_HOLY_SYMBOL_DURATION_SECONDS,
    DEFAULT_HOLY_SYMBOL_WARNING_BEFORE_EXPIRATION_SECONDS,
)


logger = logging.getLogger(__name__)


class TimerType(str, Enum):
    """Supported timer types."""

    HOLY_SYMBOL = "HOLY_SYMBOL"


class TimerNotifier(Protocol):
    """Notifier interface for timer alerts."""

    async def send(self, message: str) -> None:
        """Send a timer notification."""


@dataclass(frozen=True)
class TimerKey:
    """Unique key for one user timer in one guild."""

    guild_id: int
    user_id: int
    timer_type: TimerType


@dataclass
class TimerSession:
    """Active timer state."""

    task: asyncio.Task[None]
    expires_at: float


def format_holy_symbol_start_response(restarted: bool) -> str:
    """Return the /홀심시작 response."""
    if restarted:
        return "기존 홀심 타이머를 재시작했습니다."
    return "홀심 타이머를 시작했습니다."


def format_holy_symbol_stop_response(stopped: bool) -> str:
    """Return the /홀심중지 response."""
    if stopped:
        return "홀심 타이머를 중지했습니다."
    return "실행 중인 홀심 타이머가 없습니다."


def format_holy_symbol_status_response(remaining_seconds: int | None) -> str:
    """Return the /홀심상태 response."""
    if remaining_seconds is None:
        return "실행 중인 홀심 타이머가 없습니다."
    return f"홀심 남은 시간: {remaining_seconds}초"


def format_holy_symbol_warning_message(user_id: int) -> str:
    """Return the public warning notification."""
    return f"<@{user_id}> 🔔 홀심 10초 남음"


def format_holy_symbol_expired_message(user_id: int) -> str:
    """Return the public expiration notification."""
    return f"<@{user_id}> ✨ 홀심 다시 사용!"


class HolySymbolTimerService:
    """Manage Holy Symbol timers independently per guild and user."""

    def __init__(
        self,
        duration_seconds: int = DEFAULT_HOLY_SYMBOL_DURATION_SECONDS,
        warning_before_expiration_seconds: int = (
            DEFAULT_HOLY_SYMBOL_WARNING_BEFORE_EXPIRATION_SECONDS
        ),
        now: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.duration_seconds = duration_seconds
        self.warning_before_expiration_seconds = warning_before_expiration_seconds
        self._now = now
        self._sleep = sleep
        self._timers: dict[TimerKey, TimerSession] = {}

    def start_holy_symbol_timer(
        self,
        guild_id: int,
        user_id: int,
        notifier: TimerNotifier,
    ) -> bool:
        """Start or restart one user's Holy Symbol timer."""
        key = TimerKey(guild_id, user_id, TimerType.HOLY_SYMBOL)
        existing_timer = self._timers.get(key)
        restarted = existing_timer is not None
        if existing_timer:
            existing_timer.task.cancel()

        expires_at = self._now() + self.duration_seconds
        task = asyncio.create_task(self._run_timer(key, user_id, notifier))
        self._timers[key] = TimerSession(task=task, expires_at=expires_at)
        return restarted

    def stop_holy_symbol_timer(self, guild_id: int, user_id: int) -> bool:
        """Stop one user's Holy Symbol timer."""
        key = TimerKey(guild_id, user_id, TimerType.HOLY_SYMBOL)
        timer = self._timers.pop(key, None)
        if not timer:
            return False

        timer.task.cancel()
        return True

    def get_holy_symbol_remaining_seconds(
        self,
        guild_id: int,
        user_id: int,
    ) -> int | None:
        """Return remaining seconds for one user's Holy Symbol timer."""
        key = TimerKey(guild_id, user_id, TimerType.HOLY_SYMBOL)
        timer = self._timers.get(key)
        if not timer:
            return None

        return max(0, math.ceil(timer.expires_at - self._now()))

    def cancel_all(self) -> None:
        """Cancel all active timers."""
        for timer in self._timers.values():
            timer.task.cancel()
        self._timers.clear()

    async def _run_timer(
        self,
        key: TimerKey,
        user_id: int,
        notifier: TimerNotifier,
    ) -> None:
        try:
            warning_delay = max(
                0,
                self.duration_seconds - self.warning_before_expiration_seconds,
            )
            await self._sleep(warning_delay)
            await notifier.send(format_holy_symbol_warning_message(user_id))
            await self._sleep(self.warning_before_expiration_seconds)
            await notifier.send(format_holy_symbol_expired_message(user_id))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.error("Holy Symbol timer task failed.", exc_info=True)
        finally:
            current_timer = self._timers.get(key)
            if current_timer and current_timer.task is asyncio.current_task():
                self._timers.pop(key, None)
