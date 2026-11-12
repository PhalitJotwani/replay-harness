"""CLI entry point for replay-harness.

Usage:
  replay generate --seed 42 --count 1000 --out stream.jsonl
  replay run --input stream.jsonl --processor aggregates --out result.json
  replay compare --baseline baseline.json --actual result.json [--ignore ts] [--float-tol 1e-9]
  replay bless --actual result.json --baseline baseline.json

Exit codes: 0=match/success, 1=differences found, 2=usage/IO error
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .compare import compare as do_compare, load_json
from .generator import EventGenerator
from .processor import AggregateProcessor, AnomalyProcessor
from .recorder import Recorder
from .replayer import Replayer
from .snapshot import Snapshot, canonical_json


PROCESSORS = {
    "aggregates": AggregateProcessor,
    "anomaly": AnomalyProcessor,
}


def cmd_generate(args: argparse.Namespace) -> int:
    gen = EventGenerator(seed=args.seed)
    events = gen.generate(args.count)
    out = Path(args.out)
    Recorder.write_to_file(out, events)
    print(f"Generated {len(events)} events -> {out}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    inp = Path(args.input)
    if not inp.exists():
        print(f"Error: input file not found: {inp}", file=sys.stderr)
        return 2
    proc_cls = PROCESSORS.get(args.processor)
    if proc_cls is None:
        print(f"Error: unknown processor '{args.processor}'. Choose: {list(PROCESSORS)}", file=sys.stderr)
        return 2
    events = Recorder.read_from_file(inp)
    processor = proc_cls()
    replayer = Replayer(strict=False)
    result = replayer.replay(events, processor)
    snap = Snapshot(result)
    out = Path(args.out)
    snap.save(out)
    print(f"Processed {len(events)} events -> {out} (hash: {snap.hash()[:16]}...)")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    try:
        baseline = load_json(Path(args.baseline))
        actual = load_json(Path(args.actual))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    ignore = args.ignore or []
    tol = float(args.float_tol)
    result = do_compare(baseline, actual, ignore_fields=ignore, float_tol=tol)
    print(result.format_diff())
    return 0 if result.is_match else 1


def cmd_bless(args: argparse.Namespace) -> int:
    try:
        actual = load_json(Path(args.actual))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading actual: {e}", file=sys.stderr)
        return 2
    out = Path(args.baseline)
    out.write_text(canonical_json(actual), encoding="utf-8")
    print(f"Blessed {args.actual} -> {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replay",
        description="Deterministic event stream record-and-replay toolkit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = sub.add_parser("generate", help="Generate synthetic event stream")
    p_gen.add_argument("--seed", type=int, required=True, help="Random seed")
    p_gen.add_argument("--count", type=int, default=100, help="Number of events")
    p_gen.add_argument("--out", required=True, help="Output JSONL file")

    # run
    p_run = sub.add_parser("run", help="Run a processor over recorded events")
    p_run.add_argument("--input", required=True, help="Input JSONL file")
    p_run.add_argument("--processor", required=True, choices=list(PROCESSORS), help="Processor name")
    p_run.add_argument("--out", required=True, help="Output JSON file")

    # compare
    p_cmp = sub.add_parser("compare", help="Compare result against baseline")
    p_cmp.add_argument("--baseline", required=True, help="Baseline JSON file")
    p_cmp.add_argument("--actual", required=True, help="Actual result JSON file")
    p_cmp.add_argument("--ignore", nargs="*", metavar="FIELD", help="Fields to ignore")
    p_cmp.add_argument("--float-tol", default="1e-9", help="Float tolerance (default: 1e-9)")

    # bless
    p_bless = sub.add_parser("bless", help="Update baseline with actual result")
    p_bless.add_argument("--actual", required=True, help="Actual result JSON file")
    p_bless.add_argument("--baseline", required=True, help="Baseline file to update")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "generate": cmd_generate,
        "run": cmd_run,
        "compare": cmd_compare,
        "bless": cmd_bless,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(2)
    sys.exit(handler(args))
