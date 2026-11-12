"""Baseline comparison with structured diff."""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any

from .snapshot import canonicalize


class DiffEntry:
    """A single difference between expected and actual."""

    def __init__(self, path: str, expected: Any, actual: Any) -> None:
        self.path = path
        self.expected = expected
        self.actual = actual

    def __repr__(self) -> str:
        return f"DiffEntry(path={self.path!r}, expected={self.expected!r}, actual={self.actual!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "expected": self.expected, "actual": self.actual}


class CompareResult:
    def __init__(self, diffs: list[DiffEntry]) -> None:
        self._diffs = diffs

    @property
    def is_match(self) -> bool:
        return len(self._diffs) == 0

    @property
    def diffs(self) -> list[DiffEntry]:
        return list(self._diffs)

    def format_diff(self) -> str:
        if self.is_match:
            return "No differences found."
        lines = [f"Found {len(self._diffs)} difference(s):"]
        for d in self._diffs:
            lines.append(f"  path: {d.path}")
            lines.append(f"    expected: {d.expected!r}")
            lines.append(f"    actual:   {d.actual!r}")
        return "\n".join(lines)


def _floats_close(a: float, b: float, tol: float) -> bool:
    if math.isnan(a) and math.isnan(b):
        return True
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= tol


def _diff(
    expected: Any,
    actual: Any,
    path: str,
    diffs: list[DiffEntry],
    *,
    ignore_fields: set[str],
    float_tol: float,
) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        all_keys = set(expected.keys()) | set(actual.keys())
        for key in sorted(all_keys):
            if key in ignore_fields:
                continue
            child_path = f"{path}.{key}" if path else key
            if key not in expected:
                diffs.append(DiffEntry(child_path, "<missing>", actual[key]))
            elif key not in actual:
                diffs.append(DiffEntry(child_path, expected[key], "<missing>"))
            else:
                _diff(expected[key], actual[key], child_path, diffs,
                      ignore_fields=ignore_fields, float_tol=float_tol)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            diffs.append(DiffEntry(f"{path}[length]", len(expected), len(actual)))
        for i, (e, a) in enumerate(zip(expected, actual)):
            _diff(e, a, f"{path}[{i}]", diffs,
                  ignore_fields=ignore_fields, float_tol=float_tol)
    elif isinstance(expected, float) and isinstance(actual, (float, int)):
        if not _floats_close(expected, float(actual), float_tol):
            diffs.append(DiffEntry(path, expected, actual))
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if not _floats_close(float(expected), float(actual), float_tol):
            diffs.append(DiffEntry(path, expected, actual))
    else:
        if expected != actual:
            diffs.append(DiffEntry(path, expected, actual))


def compare(
    baseline: dict[str, Any],
    actual: dict[str, Any],
    *,
    ignore_fields: list[str] | None = None,
    float_tol: float = 1e-9,
) -> CompareResult:
    """Compare baseline to actual, returning structured diffs."""
    ignore = set(ignore_fields or [])
    b_canon = canonicalize(baseline)
    a_canon = canonicalize(actual)
    diffs: list[DiffEntry] = []
    _diff(b_canon, a_canon, "", diffs, ignore_fields=ignore, float_tol=float_tol)
    return CompareResult(diffs)


def load_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data
