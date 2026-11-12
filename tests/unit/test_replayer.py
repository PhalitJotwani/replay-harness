"""Unit tests for Replayer."""
from __future__ import annotations
import hashlib
import json
import pytest

from replay_harness.events import Event
from replay_harness.processor import AggregateProcessor
from replay_harness.replayer import Replayer, SequenceError
from replay_harness.snapshot import canonical_json


def _make_reading(seq: int, sensor_id: str = "s1", value: float = 10.0) -> Event:
    return Event(
        id=f"evt-{seq}",
        seq=seq,
        ts=float(seq),
        type="sensor.reading",
        payload={"sensor_id": sensor_id, "value": value},
    )


def _make_events(count: int) -> list[Event]:
    return [_make_reading(i, value=float(i * 10)) for i in range(1, count + 1)]


def test_replay_in_order() -> None:
    events = _make_events(5)
    proc = AggregateProcessor()
    rep = Replayer(strict=True)
    result = rep.replay(events, proc)
    assert result["total_events"] == 5
    s1 = result["sensors"]["s1"]
    assert s1["count"] == 5
    assert s1["min"] == 10.0
    assert s1["max"] == 50.0
    assert s1["sum"] == pytest.approx(150.0)
    assert s1["mean"] == pytest.approx(30.0)


def test_replay_strict_raises_on_gap() -> None:
    # seq 1, 2, 4, 5 — missing 3
    events = [_make_reading(i) for i in [1, 2, 4, 5]]
    proc = AggregateProcessor()
    rep = Replayer(strict=True)
    with pytest.raises(SequenceError):
        rep.replay(events, proc)


def test_replay_lenient_on_gap() -> None:
    events = [_make_reading(i) for i in [1, 2, 4, 5]]
    proc = AggregateProcessor()
    rep = Replayer(strict=False)
    result = rep.replay(events, proc)
    # Should complete without raising
    assert result["total_events"] == 4
    # Should have recorded a warning about the gap at seq 3
    assert len(rep.warnings) == 1
    assert "3" in rep.warnings[0]


def test_replay_out_of_order_input() -> None:
    # Provide events in reversed order
    events = list(reversed(_make_events(5)))
    proc = AggregateProcessor()
    rep = Replayer(strict=True)
    result = rep.replay(events, proc)
    # Replayer sorts by seq — should work fine
    assert result["total_events"] == 5
    assert result["sensors"]["s1"]["count"] == 5


def test_replay_deterministic_20x() -> None:
    events = _make_events(10)
    hashes = []
    for _ in range(20):
        proc = AggregateProcessor()
        rep = Replayer(strict=True)
        result = rep.replay(events, proc)
        h = hashlib.sha256(canonical_json(result).encode()).hexdigest()
        hashes.append(h)
    assert len(set(hashes)) == 1, "Replay must be deterministic across 20 runs"
