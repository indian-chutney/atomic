from __future__ import annotations

import math
import time
from dataclasses import dataclass, field


@dataclass
class TimerSession:
    total_minutes: int
    subject: str | None = None
    elapsed_seconds: float = 0.0
    running: bool = False
    started: bool = False
    _last_tick: float = field(default=0.0, init=False, repr=False)

    def set_duration(self, minutes: int) -> None:
        self.total_minutes = max(int(minutes), 0)
        self.elapsed_seconds = 0.0
        self.running = False
        self.started = False
        self._last_tick = 0.0

    @property
    def total_seconds(self) -> int:
        return self.total_minutes * 60

    def start(self, now: float | None = None) -> None:
        self.started = True
        self.running = True
        self._last_tick = time.monotonic() if now is None else now

    def tick(self, now: float | None = None) -> None:
        if not self.running:
            return
        current = time.monotonic() if now is None else now
        delta = max(current - self._last_tick, 0.0)
        self.elapsed_seconds = min(self.total_seconds, self.elapsed_seconds + delta)
        self._last_tick = current
        if self.elapsed_seconds >= self.total_seconds:
            self.running = False

    def pause(self, now: float | None = None) -> None:
        self.tick(now=now)
        self.running = False

    def resume(self, now: float | None = None) -> None:
        if self.finished:
            return
        self.running = True
        self._last_tick = time.monotonic() if now is None else now

    @property
    def finished(self) -> bool:
        return self.total_seconds > 0 and self.elapsed_seconds >= self.total_seconds

    @property
    def remaining_seconds(self) -> int:
        return max(self.total_seconds - math.floor(self.elapsed_seconds), 0)

    @property
    def productive_minutes(self) -> int:
        return max(math.floor(self.elapsed_seconds / 60), 0)

    @property
    def has_unsaved_work(self) -> bool:
        return self.started and not self.finished and (self.running or self.elapsed_seconds > 0)
