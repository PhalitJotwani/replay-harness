"""Unit tests for compare module."""
from __future__ import annotations
import pytest

from replay_harness.compare import compare, CompareResult, DiffEntry


def test_compare_identical() -> None:
    d = {"a": 1, "b": 2.0, "c": "hello"}
    result = compare(d, d)
    assert result.is_match


def test_compare_different_value() -> None:
    baseline = {"a": 1, "b": 2}
    actual = {"a": 1, "b": 99}
    result = compare(baseline, actual)
    assert not result.is_match
    assert len(result.diffs) == 1
    assert result.diffs[0].path == "b"
    assert result.diffs[0].expected == 2
    assert result.diffs[0].actual == 99


def test_compare_ignore_field() -> None:
    baseline = {"a": 1, "ts": 100}
    actual = {"a": 1, "ts": 999}
    result = compare(baseline, actual, ignore_fields=["ts"])
    assert result.is_match


def test_compare_float_tolerance() -> None:
    # Within tolerance → match
    baseline = {"v": 1.0}
    actual = {"v": 1.0 + 1e-10}
    result = compare(baseline, actual, float_tol=1e-9)
    assert result.is_match

    # Outside tolerance → diff
    actual2 = {"v": 1.0 + 1e-8}
    result2 = compare(baseline, actual2, float_tol=1e-9)
    assert not result2.is_match


def test_compare_nested_dict() -> None:
    baseline = {"outer": {"inner": {"deep": 42}}}
    actual = {"outer": {"inner": {"deep": 99}}}
    result = compare(baseline, actual)
    assert not result.is_match
    assert len(result.diffs) == 1
    assert result.diffs[0].path == "outer.inner.deep"


def test_compare_missing_key() -> None:
    baseline = {"a": 1, "b": 2}
    actual = {"a": 1}
    result = compare(baseline, actual)
    assert not result.is_match
    paths = [d.path for d in result.diffs]
    assert "b" in paths
    missing_diff = next(d for d in result.diffs if d.path == "b")
    assert missing_diff.actual == "<missing>"


def test_format_diff_no_diffs() -> None:
    result = compare({"x": 1}, {"x": 1})
    assert result.format_diff() == "No differences found."


def test_format_diff_with_diffs() -> None:
    result = compare({"x": 1}, {"x": 2})
    text = result.format_diff()
    assert "expected" in text
    assert "actual" in text
