"""Unit tests for snapshot.py."""
from __future__ import annotations
import json

import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

from replay_harness.snapshot import (
    Snapshot,
    canonical_hash,
    canonical_json,
    canonicalize,
)


# ------------------------------------------------------------------
# canonicalize
# ------------------------------------------------------------------

def test_canonicalize_sorts_dict_keys():
    obj = {"z": 1, "a": 2, "m": 3}
    result = canonicalize(obj)
    assert list(result.keys()) == ["a", "m", "z"]


def test_canonicalize_nested_dict_sorted():
    obj = {"b": {"y": 1, "x": 2}, "a": 0}
    result = canonicalize(obj)
    assert list(result.keys()) == ["a", "b"]
    assert list(result["b"].keys()) == ["x", "y"]


def test_canonicalize_normalizes_floats():
    result = canonicalize(1.123456789999)
    # rounds to 9 decimal places
    assert result == round(1.123456789999, 9)


def test_canonicalize_list_order_preserved():
    obj = [3, 1, 2]
    assert canonicalize(obj) == [3, 1, 2]


def test_canonicalize_tuple_becomes_list():
    result = canonicalize((1, 2, 3))
    assert result == [1, 2, 3]


def test_canonicalize_scalars_passthrough():
    assert canonicalize(None) is None
    assert canonicalize(True) is True
    assert canonicalize(42) == 42
    assert canonicalize("hello") == "hello"


# ------------------------------------------------------------------
# canonical_json
# ------------------------------------------------------------------

def test_canonical_json_trailing_newline():
    s = canonical_json({"a": 1})
    assert s.endswith("\n")


def test_canonical_json_sorted_keys():
    s = canonical_json({"z": 1, "a": 2})
    parsed = json.loads(s)
    assert list(parsed.keys()) == ["a", "z"]


def test_canonical_json_compact_separators():
    s = canonical_json({"a": 1})
    # compact: no space after colon or comma
    assert " " not in s.strip()


# ------------------------------------------------------------------
# canonical_hash
# ------------------------------------------------------------------

def test_canonical_hash_stable():
    obj = {"foo": "bar", "num": 42}
    h1 = canonical_hash(obj)
    h2 = canonical_hash(obj)
    assert h1 == h2


def test_canonical_hash_is_sha256_hex():
    h = canonical_hash({"x": 1})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_canonical_hash_different_objects_differ():
    h1 = canonical_hash({"a": 1})
    h2 = canonical_hash({"a": 2})
    assert h1 != h2


def test_canonical_hash_key_order_invariant():
    h1 = canonical_hash({"a": 1, "b": 2})
    h2 = canonical_hash({"b": 2, "a": 1})
    assert h1 == h2


# ------------------------------------------------------------------
# Snapshot class
# ------------------------------------------------------------------

def test_snapshot_data_property():
    data = {"result": 42}
    snap = Snapshot(data)
    assert snap.data == data


def test_snapshot_hash_matches_canonical_hash():
    data = {"x": 1, "y": 2}
    snap = Snapshot(data)
    assert snap.hash() == canonical_hash(data)


def test_snapshot_save_load_roundtrip(tmp_path):
    data = {"answer": 42, "nested": {"k": [1, 2, 3]}}
    snap = Snapshot(data)
    path = tmp_path / "snap.json"
    snap.save(path)
    loaded = Snapshot.load(path)
    assert loaded.data == data


def test_snapshot_save_produces_valid_json(tmp_path):
    data = {"a": 1}
    Snapshot(data).save(tmp_path / "s.json")
    text = (tmp_path / "s.json").read_text(encoding="utf-8")
    assert json.loads(text) == data


def test_snapshot_to_canonical_json_matches_function():
    data = {"z": 9, "a": 1}
    snap = Snapshot(data)
    assert snap.to_canonical_json() == canonical_json(data)


# ------------------------------------------------------------------
# Hypothesis: canonicalize is idempotent
# ------------------------------------------------------------------

simple_values = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1000, max_value=1000),
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        st.text(max_size=10),
    ),
    lambda children: st.lists(children, max_size=4)
    | st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=4),
    max_leaves=15,
)


@given(obj=simple_values)
@settings(max_examples=200)
def test_canonicalize_idempotent(obj):
    once = canonicalize(obj)
    twice = canonicalize(once)
    assert once == twice
