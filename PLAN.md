# replay-harness Build Plan

## Layer 1: Core Data Model (`events.py`)

The build begins with `events.py`, which defines the fundamental `Event` dataclass. This frozen dataclass holds the five canonical fields — `id`, `seq`, `ts`, `type`, and `payload` — and provides deterministic JSON serialization via `to_json()` (using sorted keys) and deserialization via `from_json()`. Everything else depends on `Event`, so it must be rock-solid first. No external dependencies; the only imports are from the standard library (`json`, `dataclasses`).

## Layer 2: Time Abstraction (`clock.py`)

Next comes `clock.py`, the injectable clock abstraction. The abstract `Clock` base class declares a single `now() -> float` method. `SystemClock` delegates to `time.time()`, while `FakeClock` maintains an internal counter that can be advanced deterministically. This layer is a pure utility with no dependencies on the rest of the library. Making it a first-class object — rather than patching `time.time()` in tests — keeps every other module honest and testable without monkeypatching.

## Layer 3: Recording Infrastructure (`recorder.py` and `snapshot.py`)

With the data model and clock in place, `recorder.py` can be built. `Recorder` accepts a `Clock` at construction, maintains a monotonically increasing sequence counter, and exposes `record()` (creates an `Event` in memory), `write_event()` (creates and serialises to a file object), and static helpers `write_to_file` / `read_from_file` for batch JSONL I/O. Alongside it, `snapshot.py` provides the canonicalization pipeline: `canonicalize()` normalises dict key order and float precision, `canonical_json()` serialises to a stable string, `canonical_hash()` produces a SHA-256 digest, and the `Snapshot` class wraps a result dict with `save()` / `load()` persistence. These two modules are independent of each other and can be developed in parallel.

## Layer 4: Public API and Verification (`__init__.py`, tests, CLI)

The package `__init__.py` re-exports the public surface (`Event`, `Clock`, `FakeClock`, `SystemClock`, `Recorder`, `Snapshot`, `canonical_hash`, `canonical_json`, `canonicalize`). Unit tests are written for each of the four modules using `pytest` and `hypothesis`, targeting ≥ 90 % line coverage. Integration tests (owned by other workers) depend on the higher-level modules `replayer.py`, `processor.py`, `compare.py`, and `cli.py`, which build on this foundation layer without modifying it.
