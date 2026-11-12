"""Seeded synthetic event generator. Same seed => same stream, always."""
from __future__ import annotations
import random
import uuid
from typing import Any

from .clock import Clock, FakeClock
from .events import Event

# Synthetic IoT sensor data
SENSOR_IDS = ["sensor-A1", "sensor-B2", "sensor-C3", "sensor-D4", "sensor-E5"]
EVENT_TYPES = ["sensor.reading", "sensor.reading", "sensor.reading", "order.placed", "order.shipped"]
# (sensor.reading appears 3x to make it more likely)


class EventGenerator:
    """Deterministic synthetic event generator.

    Uses seeded random.Random — no call to random module-level functions.
    Uses an injectable FakeClock — no call to time.time().
    Same seed => same sequence of events.
    """

    def __init__(self, seed: int, clock: Clock | None = None) -> None:
        self._rng = random.Random(seed)
        self._clock = clock or FakeClock(start=1_700_000_000.0, step=1.0)
        self._seq = 0

    def _next_uuid(self) -> str:
        """Generate a deterministic UUID using seeded RNG."""
        return str(uuid.UUID(int=self._rng.getrandbits(128), version=4))

    def _sensor_reading_payload(self) -> dict[str, Any]:
        return {
            "sensor_id": self._rng.choice(SENSOR_IDS),
            "unit": "celsius",
            "value": round(self._rng.uniform(-20.0, 150.0), 4),
        }

    def _order_payload(self, event_type: str) -> dict[str, Any]:
        order_id = f"ORD-{self._rng.randint(10000, 99999)}"
        payload: dict[str, Any] = {
            "customer_id": f"CUST-{self._rng.randint(1000, 9999)}",
            "order_id": order_id,
        }
        if event_type == "order.placed":
            payload["total_usd"] = round(self._rng.uniform(5.0, 500.0), 2)
            payload["items"] = self._rng.randint(1, 10)
        elif event_type == "order.shipped":
            payload["carrier"] = self._rng.choice(["FedEx", "UPS", "USPS", "DHL"])
        return payload

    def generate_one(self) -> Event:
        """Generate a single synthetic event."""
        self._seq += 1
        event_type = self._rng.choice(EVENT_TYPES)
        if event_type == "sensor.reading":
            payload = self._sensor_reading_payload()
        else:
            payload = self._order_payload(event_type)
        ts = self._clock.now()
        if hasattr(self._clock, "advance"):
            self._clock.advance()  # type: ignore[union-attr]
        return Event(
            id=self._next_uuid(),
            seq=self._seq,
            ts=ts,
            type=event_type,
            payload=payload,
        )

    def generate(self, count: int) -> list[Event]:
        """Generate `count` synthetic events deterministically."""
        return [self.generate_one() for _ in range(count)]
