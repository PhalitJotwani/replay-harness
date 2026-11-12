"""Event dataclass with JSON (de)serialization."""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Event:
    id: str
    seq: int
    ts: float
    type: str
    payload: dict[str, Any] = field(default_factory=dict, compare=True)

    def to_json(self) -> str:
        """Serialize to canonical JSON (sorted keys)."""
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> "Event":
        """Deserialize from JSON string."""
        data = json.loads(s)
        return cls(
            id=data["id"],
            seq=data["seq"],
            ts=data["ts"],
            type=data["type"],
            payload=data.get("payload", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
