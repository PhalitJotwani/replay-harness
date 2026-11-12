"""Deterministic replay engine."""
from __future__ import annotations
from typing import Any, TYPE_CHECKING

from .events import Event

if TYPE_CHECKING:
    from .processor import Processor


class SequenceError(Exception):
    """Raised when events arrive out-of-sequence."""
    pass


class Replayer:
    """Feeds events to a Processor in recorded order.

    Args:
        strict: if True, raise SequenceError on gap/out-of-order. If False, log warning and continue.
    """

    def __init__(self, strict: bool = True) -> None:
        self._strict = strict
        self._expected_seq = 1
        self._warnings: list[str] = []

    @property
    def warnings(self) -> list[str]:
        return list(self._warnings)

    def replay(self, events: list[Event], processor: "Processor") -> dict[str, Any]:
        """Replay events through processor in sequence order. Returns processor result."""
        # Sort by seq to ensure deterministic order regardless of input order
        sorted_events = sorted(events, key=lambda e: e.seq)
        self._expected_seq = 1
        self._warnings = []

        for evt in sorted_events:
            if evt.seq != self._expected_seq:
                msg = f"Sequence gap: expected {self._expected_seq}, got {evt.seq}"
                if self._strict:
                    raise SequenceError(msg)
                else:
                    self._warnings.append(msg)
            self._expected_seq = evt.seq + 1
            processor.process(evt)

        return processor.result()
