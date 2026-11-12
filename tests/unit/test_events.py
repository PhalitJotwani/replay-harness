"""Unit tests for events.py."""
from __future__ import annotations
import json
import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

from replay_harness.events import Event


def make_event(**kwargs):
    defaults = dict(id="abc-123", seq=1, ts=1000.0, type="click", payload={})
    defaults.update(kwargs)
    return Event(**defaults)


# ------------------------------------------------------------------
# Basic tests
# ------------------------------------------------------------------

def test_event_roundtrip():
    evt = make_event(payload={"x": 1})
    assert Event.from_json(evt.to_json()) == evt


def test_event_to_json_sorted_keys():
    evt = make_event()
    parsed = json.loads(evt.to_json())
    keys = list(parsed.keys())
    assert keys == sorted(keys)


def test_event_frozen():
    evt = make_event()
    with pytest.raises((AttributeError, TypeError)):
        evt.id = "new-id"  # type: ignore[misc]


def test_event_payload_preserved():
    payload = {"nested": {"a": [1, 2, 3], "b": None}, "flag": True}
    evt = make_event(payload=payload)
    result = Event.from_json(evt.to_json())
    assert result.payload == payload


def test_event_to_dict():
    evt = make_event(payload={"k": "v"})
    d = evt.to_dict()
    assert d["id"] == evt.id
    assert d["payload"] == {"k": "v"}


def test_event_from_json_missing_payload_defaults_to_empty():
    raw = json.dumps({"id": "x", "seq": 1, "ts": 0.0, "type": "t"})
    evt = Event.from_json(raw)
    assert evt.payload == {}


# ------------------------------------------------------------------
# Hypothesis property test
# ------------------------------------------------------------------

printable_text = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc")),
    min_size=1,
    max_size=20,
)

json_values = st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()),
    lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3),
    max_leaves=10,
)


@given(
    id_=printable_text,
    seq=st.integers(min_value=0, max_value=10_000),
    ts=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
    type_=printable_text,
)
@settings(max_examples=100)
def test_event_roundtrip_hypothesis(id_: str, seq: int, ts: float, type_: str):
    evt = Event(id=id_, seq=seq, ts=ts, type=type_, payload={})
    assert Event.from_json(evt.to_json()) == evt
