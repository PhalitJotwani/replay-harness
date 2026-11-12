"""Append-only JSONL recorder with monotonically increasing sequence numbers."""
from __future__ import annotations
import uuid
from pathlib import Path
from typing import IO, Any

from .clock import Clock, SystemClock
from .events import Event


class Recorder:
    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or SystemClock()
        self._seq = 0

    @property
    def seq(self) -> int:
        return self._seq

    def record(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        event_id: str | None = None,
    ) -> Event:
        """Create and return an Event (does not write anywhere)."""
        self._seq += 1
        return Event(
            id=event_id or str(uuid.uuid4()),
            seq=self._seq,
            ts=self._clock.now(),
            type=event_type,
            payload=payload,
        )

    def write_event(
        self,
        f: IO[str],
        event_type: str,
        payload: dict[str, Any],
        *,
        event_id: str | None = None,
    ) -> Event:
        """Record an event and write it to a file object as JSONL."""
        evt = self.record(event_type, payload, event_id=event_id)
        f.write(evt.to_json() + "\n")
        return evt

    @staticmethod
    def write_to_file(path: Path, events: list[Event]) -> None:
        """Write a list of events to a JSONL file."""
        with open(path, "w", encoding="utf-8") as f:
            for evt in events:
                f.write(evt.to_json() + "\n")

    @staticmethod
    def read_from_file(path: Path) -> list[Event]:
        """Read events from a JSONL file."""
        events: list[Event] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(Event.from_json(line))
        return events
