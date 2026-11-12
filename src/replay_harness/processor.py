"""Processor protocol and two example implementations."""
from __future__ import annotations
from typing import Any, Protocol, runtime_checkable

from .events import Event


@runtime_checkable
class Processor(Protocol):
    def process(self, event: Event) -> None: ...
    def result(self) -> dict[str, Any]: ...
    def reset(self) -> None: ...


class AggregateProcessor:
    """Running aggregates over numeric payload fields.

    For events of type 'sensor.reading' with payload {'sensor_id': str, 'value': float},
    computes per-sensor: count, sum, min, max, mean.
    """

    def __init__(self) -> None:
        self._stats: dict[str, dict[str, Any]] = {}
        self._total_events = 0

    def process(self, event: Event) -> None:
        self._total_events += 1
        if event.type != "sensor.reading":
            return
        sensor_id = str(event.payload.get("sensor_id", "unknown"))
        value = float(event.payload.get("value", 0.0))
        if sensor_id not in self._stats:
            self._stats[sensor_id] = {"count": 0, "sum": 0.0, "min": value, "max": value}
        s = self._stats[sensor_id]
        s["count"] += 1
        s["sum"] += value
        s["min"] = min(s["min"], value)
        s["max"] = max(s["max"], value)

    def result(self) -> dict[str, Any]:
        out: dict[str, Any] = {"total_events": self._total_events, "sensors": {}}
        for sid, s in sorted(self._stats.items()):
            mean = s["sum"] / s["count"] if s["count"] > 0 else 0.0
            out["sensors"][sid] = {
                "count": s["count"],
                "max": s["max"],
                "mean": mean,
                "min": s["min"],
                "sum": s["sum"],
            }
        return out

    def reset(self) -> None:
        self._stats = {}
        self._total_events = 0


class AnomalyProcessor:
    """Simple threshold-based anomaly flagging.

    For events of type 'sensor.reading', flags readings outside [low, high] bounds.
    """

    def __init__(self, low: float = 0.0, high: float = 100.0) -> None:
        self._low = low
        self._high = high
        self._anomalies: list[dict[str, Any]] = []
        self._total = 0

    def process(self, event: Event) -> None:
        self._total += 1
        if event.type != "sensor.reading":
            return
        value = float(event.payload.get("value", 0.0))
        if value < self._low or value > self._high:
            self._anomalies.append({
                "event_id": event.id,
                "seq": event.seq,
                "sensor_id": event.payload.get("sensor_id", "unknown"),
                "value": value,
            })

    def result(self) -> dict[str, Any]:
        return {
            "anomalies": sorted(self._anomalies, key=lambda x: x["seq"]),
            "anomaly_count": len(self._anomalies),
            "total_events": self._total,
        }

    def reset(self) -> None:
        self._anomalies = []
        self._total = 0
