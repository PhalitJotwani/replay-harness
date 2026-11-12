"""Canonicalize output and compute stable hashes."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def _normalize_float(v: float, precision: int = 9) -> float:
    if math.isnan(v) or math.isinf(v):
        return v
    return round(v, precision)


def canonicalize(obj: Any, *, float_precision: int = 9) -> Any:
    """Return canonical form: sorted dict keys, normalized floats, stable list order."""
    if isinstance(obj, dict):
        return {k: canonicalize(v, float_precision=float_precision) for k in sorted(obj.keys())}
    elif isinstance(obj, (list, tuple)):
        return [canonicalize(v, float_precision=float_precision) for v in obj]
    elif isinstance(obj, float):
        return _normalize_float(obj, float_precision)
    else:
        return obj


def canonical_json(obj: Any, *, float_precision: int = 9) -> str:
    """Serialize obj to canonical JSON string with trailing newline."""
    canon = canonicalize(obj, float_precision=float_precision)
    return json.dumps(canon, sort_keys=True, separators=(",", ":")) + "\n"


def canonical_hash(obj: Any, *, float_precision: int = 9) -> str:
    """Return SHA-256 hex digest of the canonical JSON representation."""
    data = canonical_json(obj, float_precision=float_precision)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class Snapshot:
    """Wraps a result dict with canonical serialization."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def data(self) -> dict[str, Any]:
        return self._data

    def to_canonical_json(self, *, float_precision: int = 9) -> str:
        return canonical_json(self._data, float_precision=float_precision)

    def hash(self, *, float_precision: int = 9) -> str:
        return canonical_hash(self._data, float_precision=float_precision)

    def save(self, path: Path) -> None:
        path.write_text(self.to_canonical_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Snapshot":
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return cls(data)
