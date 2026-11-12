"""Unit tests for clock.py."""
from __future__ import annotations
import time

from replay_harness.clock import FakeClock, SystemClock


def test_fake_clock_starts_at_zero():
    clk = FakeClock()
    assert clk.now() == 0.0


def test_fake_clock_starts_at_custom_value():
    clk = FakeClock(start=42.5)
    assert clk.now() == 42.5


def test_fake_clock_advance_default_step():
    clk = FakeClock(start=0.0, step=1.0)
    clk.advance()
    assert clk.now() == 1.0
    clk.advance()
    assert clk.now() == 2.0


def test_fake_clock_advance_custom_delta():
    clk = FakeClock(start=10.0)
    clk.advance(5.5)
    assert clk.now() == 15.5


def test_fake_clock_set_time():
    clk = FakeClock(start=100.0)
    clk.set_time(0.0)
    assert clk.now() == 0.0


def test_fake_clock_advance_none_uses_step():
    clk = FakeClock(start=0.0, step=3.0)
    clk.advance(None)
    assert clk.now() == 3.0


def test_system_clock_returns_float():
    clk = SystemClock()
    t = clk.now()
    assert isinstance(t, float)
    assert t > 0


def test_system_clock_monotone():
    clk = SystemClock()
    t1 = clk.now()
    time.sleep(0.01)
    t2 = clk.now()
    assert t2 >= t1
