"""Injectable clock abstraction. No other module calls time.time() directly."""
from __future__ import annotations
import time
from abc import ABC, abstractmethod


class Clock(ABC):
    @abstractmethod
    def now(self) -> float: ...


class SystemClock(Clock):
    def now(self) -> float:
        return time.time()


class FakeClock(Clock):
    def __init__(self, start: float = 0.0, step: float = 1.0) -> None:
        self._current = start
        self._step = step

    def now(self) -> float:
        return self._current

    def advance(self, delta: float | None = None) -> None:
        self._current += delta if delta is not None else self._step

    def set_time(self, t: float) -> None:
        self._current = t
