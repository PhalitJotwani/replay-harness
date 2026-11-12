"""Unit tests for recorder.py."""
from __future__ import annotations
import io

from replay_harness.clock import FakeClock
from replay_harness.events import Event
from replay_harness.recorder import Recorder


def test_seq_increments_monotonically():
    rec = Recorder()
    seqs = [rec.record("t", {}).seq for _ in range(5)]
    assert seqs == [1, 2, 3, 4, 5]


def test_initial_seq_is_zero():
    rec = Recorder()
    assert rec.seq == 0


def test_uses_clock_time():
    clk = FakeClock(start=42.0, step=1.0)
    rec = Recorder(clock=clk)
    evt = rec.record("ping", {})
    assert evt.ts == 42.0


def test_clock_not_advanced_by_record():
    """Recorder.record() reads the clock but does not advance FakeClock."""
    clk = FakeClock(start=5.0)
    rec = Recorder(clock=clk)
    rec.record("a", {})
    rec.record("b", {})
    assert clk.now() == 5.0  # FakeClock only advances when advance() is called


def test_explicit_event_id():
    rec = Recorder()
    evt = rec.record("t", {}, event_id="fixed-id")
    assert evt.id == "fixed-id"


def test_auto_event_id_is_uuid_string():
    rec = Recorder()
    evt = rec.record("t", {})
    # UUIDs are 36 chars: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    assert len(evt.id) == 36
    assert evt.id.count("-") == 4


def test_write_read_roundtrip(tmp_path):
    clk = FakeClock(start=1.0, step=1.0)
    rec = Recorder(clock=clk)
    events = []
    for i in range(3):
        events.append(rec.record(f"type_{i}", {"i": i}))
    path = tmp_path / "events.jsonl"
    Recorder.write_to_file(path, events)
    loaded = Recorder.read_from_file(path)
    assert loaded == events


def test_write_event_to_fileobj():
    clk = FakeClock(start=0.0)
    rec = Recorder(clock=clk)
    buf = io.StringIO()
    evt = rec.write_event(buf, "click", {"x": 10}, event_id="id-1")
    buf.seek(0)
    line = buf.readline().strip()
    assert line != ""
    loaded = Event.from_json(line)
    assert loaded == evt


def test_write_event_jsonl_line_ends_with_newline():
    rec = Recorder()
    buf = io.StringIO()
    rec.write_event(buf, "t", {})
    assert buf.getvalue().endswith("\n")


def test_read_from_file_skips_blank_lines(tmp_path):
    path = tmp_path / "events.jsonl"
    evt = Event(id="x", seq=1, ts=0.0, type="t", payload={})
    path.write_text(evt.to_json() + "\n\n", encoding="utf-8")
    loaded = Recorder.read_from_file(path)
    assert len(loaded) == 1
    assert loaded[0] == evt
