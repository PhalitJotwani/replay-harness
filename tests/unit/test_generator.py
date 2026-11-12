"""Tests for generator.py"""
import pytest
from hypothesis import given, settings, strategies as st
from replay_harness.generator import EventGenerator


def test_same_seed_same_stream():
    g1 = EventGenerator(seed=42)
    g2 = EventGenerator(seed=42)
    events1 = g1.generate(100)
    events2 = g2.generate(100)
    assert events1 == events2


def test_different_seeds_different_streams():
    g1 = EventGenerator(seed=42)
    g2 = EventGenerator(seed=99)
    e1 = g1.generate(10)
    e2 = g2.generate(10)
    assert e1 != e2


def test_sequence_numbers_monotonic():
    gen = EventGenerator(seed=1)
    events = gen.generate(50)
    seqs = [e.seq for e in events]
    assert seqs == list(range(1, 51))


def test_event_types_valid():
    gen = EventGenerator(seed=7)
    events = gen.generate(200)
    valid_types = {"sensor.reading", "order.placed", "order.shipped"}
    for e in events:
        assert e.type in valid_types


def test_sensor_readings_have_required_fields():
    gen = EventGenerator(seed=3)
    events = gen.generate(100)
    for e in events:
        if e.type == "sensor.reading":
            assert "sensor_id" in e.payload
            assert "value" in e.payload
            assert "unit" in e.payload


@given(st.integers(min_value=0, max_value=10000))
def test_property_same_seed_same_stream(seed):
    g1 = EventGenerator(seed=seed)
    g2 = EventGenerator(seed=seed)
    assert g1.generate(10) == g2.generate(10)
