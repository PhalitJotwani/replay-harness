"""Unit tests for Processor implementations."""
from __future__ import annotations
import pytest

from replay_harness.events import Event
from replay_harness.processor import AggregateProcessor, AnomalyProcessor, Processor


def _reading(seq: int, sensor_id: str, value: float) -> Event:
    return Event(
        id=f"evt-{seq}",
        seq=seq,
        ts=float(seq),
        type="sensor.reading",
        payload={"sensor_id": sensor_id, "value": value},
    )


def test_aggregate_basic() -> None:
    proc = AggregateProcessor()
    for seq, val in enumerate([10.0, 20.0, 30.0], start=1):
        proc.process(_reading(seq, "A", val))
    result = proc.result()
    assert result["total_events"] == 3
    s = result["sensors"]["A"]
    assert s["count"] == 3
    assert s["sum"] == pytest.approx(60.0)
    assert s["min"] == pytest.approx(10.0)
    assert s["max"] == pytest.approx(30.0)
    assert s["mean"] == pytest.approx(20.0)


def test_aggregate_multiple_sensors() -> None:
    proc = AggregateProcessor()
    proc.process(_reading(1, "A", 5.0))
    proc.process(_reading(2, "B", 50.0))
    proc.process(_reading(3, "A", 15.0))
    result = proc.result()
    assert "A" in result["sensors"]
    assert "B" in result["sensors"]
    assert result["sensors"]["A"]["count"] == 2
    assert result["sensors"]["B"]["count"] == 1
    assert result["sensors"]["A"]["mean"] == pytest.approx(10.0)


def test_aggregate_reset() -> None:
    proc = AggregateProcessor()
    proc.process(_reading(1, "A", 100.0))
    proc.reset()
    result = proc.result()
    assert result["total_events"] == 0
    assert result["sensors"] == {}


def test_anomaly_flags_outliers() -> None:
    proc = AnomalyProcessor(low=0.0, high=100.0)
    proc.process(_reading(1, "A", 50.0))   # normal
    proc.process(_reading(2, "A", 150.0))  # above high
    proc.process(_reading(3, "A", -10.0))  # below low
    result = proc.result()
    assert result["anomaly_count"] == 2
    assert result["total_events"] == 3
    seqs = [a["seq"] for a in result["anomalies"]]
    assert 2 in seqs
    assert 3 in seqs
    assert 1 not in seqs


def test_anomaly_no_false_positives() -> None:
    proc = AnomalyProcessor(low=0.0, high=100.0)
    for i, v in enumerate([10.0, 50.0, 99.9, 0.0, 100.0], start=1):
        proc.process(_reading(i, "A", v))
    result = proc.result()
    assert result["anomaly_count"] == 0


def test_processor_protocol() -> None:
    proc = AggregateProcessor()
    assert isinstance(proc, Processor), "AggregateProcessor must satisfy the Processor protocol"
