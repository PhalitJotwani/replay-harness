"""Tests for cli.py"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import pytest

from replay_harness.cli import (
    build_parser,
    cmd_bless,
    cmd_compare,
    cmd_generate,
    cmd_run,
    main,
)
from replay_harness.generator import EventGenerator
from replay_harness.recorder import Recorder
from replay_harness.snapshot import Snapshot, canonical_json


def test_build_parser_has_subcommands():
    parser = build_parser()
    # Verify parser is an ArgumentParser
    assert isinstance(parser, argparse.ArgumentParser)
    # Parse each subcommand to check it's registered
    for cmd in ("generate", "run", "compare", "bless"):
        # just check parse_known_args doesn't crash on the subcommand name
        ns, _ = parser.parse_known_args([cmd, "--help"] if False else [cmd])
        # ns.command will only be set when required args provided; just verify
        # the subparser is registered
    # Verify required subcommand error
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_subcommands_registered():
    parser = build_parser()
    # generate sub-parser
    args = parser.parse_args(["generate", "--seed", "42", "--out", "x.jsonl"])
    assert args.command == "generate"
    assert args.seed == 42

    args = parser.parse_args(["run", "--input", "x.jsonl", "--processor", "aggregates", "--out", "r.json"])
    assert args.command == "run"

    args = parser.parse_args(["compare", "--baseline", "b.json", "--actual", "a.json"])
    assert args.command == "compare"

    args = parser.parse_args(["bless", "--actual", "a.json", "--baseline", "b.json"])
    assert args.command == "bless"


def test_cmd_generate_creates_file(tmp_path):
    out = tmp_path / "stream.jsonl"
    args = argparse.Namespace(seed=42, count=50, out=str(out))
    rc = cmd_generate(args)
    assert rc == 0
    assert out.exists()
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 50


def test_cmd_run_creates_output(tmp_path):
    # First generate a stream
    stream = tmp_path / "stream.jsonl"
    gen_args = argparse.Namespace(seed=7, count=20, out=str(stream))
    cmd_generate(gen_args)

    # Then run aggregates processor
    result = tmp_path / "result.json"
    run_args = argparse.Namespace(input=str(stream), processor="aggregates", out=str(result))
    rc = cmd_run(run_args)
    assert rc == 0
    assert result.exists()
    data = json.loads(result.read_text(encoding="utf-8"))
    assert "total_events" in data


def test_cmd_run_missing_input_returns_2(tmp_path):
    run_args = argparse.Namespace(
        input=str(tmp_path / "nonexistent.jsonl"),
        processor="aggregates",
        out=str(tmp_path / "result.json"),
    )
    rc = cmd_run(run_args)
    assert rc == 2


def test_cmd_compare_match_returns_0(tmp_path):
    # Create two identical JSON files
    data = {"total_events": 10, "sensors": {}}
    f1 = tmp_path / "baseline.json"
    f2 = tmp_path / "actual.json"
    text = canonical_json(data)
    f1.write_text(text, encoding="utf-8")
    f2.write_text(text, encoding="utf-8")

    args = argparse.Namespace(baseline=str(f1), actual=str(f2), ignore=None, float_tol="1e-9")
    rc = cmd_compare(args)
    assert rc == 0


def test_cmd_compare_mismatch_returns_1(tmp_path):
    f1 = tmp_path / "baseline.json"
    f2 = tmp_path / "actual.json"
    f1.write_text(canonical_json({"total_events": 10}), encoding="utf-8")
    f2.write_text(canonical_json({"total_events": 20}), encoding="utf-8")

    args = argparse.Namespace(baseline=str(f1), actual=str(f2), ignore=None, float_tol="1e-9")
    rc = cmd_compare(args)
    assert rc == 1


def test_cmd_compare_missing_file_returns_2(tmp_path):
    args = argparse.Namespace(
        baseline=str(tmp_path / "nope.json"),
        actual=str(tmp_path / "also_nope.json"),
        ignore=None,
        float_tol="1e-9",
    )
    rc = cmd_compare(args)
    assert rc == 2


def test_cmd_bless_writes_baseline(tmp_path):
    actual = tmp_path / "result.json"
    baseline = tmp_path / "baseline.json"
    actual.write_text(canonical_json({"total_events": 5}), encoding="utf-8")

    args = argparse.Namespace(actual=str(actual), baseline=str(baseline))
    rc = cmd_bless(args)
    assert rc == 0
    assert baseline.exists()
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["total_events"] == 5


def test_cmd_bless_missing_actual_returns_2(tmp_path):
    args = argparse.Namespace(
        actual=str(tmp_path / "nope.json"),
        baseline=str(tmp_path / "baseline.json"),
    )
    rc = cmd_bless(args)
    assert rc == 2


def test_main_exits_on_no_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["replay"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code != 0
