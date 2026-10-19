#!/usr/bin/env python3
"""Per-module coverage gate (plan section 6.5 job 2; BLOCKS merge).

Reads ``coverage.json`` (as produced by ``uv run coverage json -o cov.json``)
and asserts every gated module meets the per-module floor. Phase 1 gates the
core set; Phase 2 adds ``frontends/python.py`` by appending to
:data:`GATED_MODULES` (json format 2, verified against coverage.py 7.5.4:
per-file ``summary`` carries ``covered_lines``/``covered_branches``/
``num_statements``/``num_branches`` when ``branch = true``).

Usage::

    uv run coverage json -o cov.json && uv run python scripts/coverage_gate.py

Exit codes: 0 = gate passed, 1 = usage error, 2 = gate failure.
Pure stdlib.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

# The Phase-1 gated set (plan section 6.5); Phase 2 appends
# "frontends/python.py" here and nowhere else.
GATED_MODULES: Final[frozenset[str]] = frozenset(
    {
        "ir.py",
        "errors.py",
        "fs_guard.py",
        "limits.py",
    }
)

CODE_FLOOR: Final[float] = 90.0
EXIT_OK: Final[int] = 0
EXIT_USAGE: Final[int] = 1
EXIT_GATE_FAILED: Final[int] = 2


def _module_name(path: str) -> str | None:
    """Map a coverage.json file key to ``<module>.py`` or None (not gated).

    coverage.py emits absolute paths when it can (relative otherwise, and
    backslash-separated on Windows); normalizing separators and taking the
    basename suffices because gated modules have unique filenames.
    """
    base = path.replace("\\\\", "/").rsplit("/", 1)[-1]
    return base if base in GATED_MODULES else None


def _percent(summary: Mapping[str, object]) -> float:
    """Coverage percent = (covered lines + covered branches) / measurable.

    Recomputed from the integer parts rather than trusting
    ``percent_covered_display``, so the gate is independent of json format
    tweaks. An empty module (nothing measurable) counts as fully covered.
    """
    covered = int(summary.get("covered_lines", 0)) + int(
        summary.get("covered_branches", 0)
    )
    total = int(summary.get("num_statements", 0)) + int(summary.get("num_branches", 0))
    if total == 0:
        return 100.0
    return 100.0 * covered / total


def evaluate(data: Mapping[str, object]) -> dict[str, float]:
    """Return ``{module: percent}`` for the gated set, sorted by module.

    A gated module missing from the report is scored 0.0% -- a module that
    fails to compile or is excluded from the report must not silently pass.
    """
    files = data.get("files", {})
    if not isinstance(files, dict):
        raise TypeError("'files' is not an object")
    found: dict[str, float] = {}
    for key, entry in files.items():
        if not isinstance(key, str):
            raise TypeError("file key is not a string")
        module = _module_name(key)
        if module is None or not isinstance(entry, dict):
            continue
        summary = entry.get("summary")
        if not isinstance(summary, dict):
            raise TypeError(f"'summary' is not an object for {key}")
        found[module] = _percent(summary)
    return {module: found.get(module, 0.0) for module in sorted(GATED_MODULES)}


def _table(percents: Mapping[str, float], floor: float) -> str:
    """Render the gate table; one row per gated module."""
    header = f"{'module':<16} {'coverage':>9} {'floor':>6} {'gate':>5}"
    lines = [header, "-" * len(header)]
    for module in sorted(percents):
        percent = percents[module]
        verdict = "ok" if percent >= floor else "FAIL"
        lines.append(f"{module:<16} {percent:>8.1f}% {floor:>6.1f} {verdict:>5}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Parse args, evaluate the gate, print the table, return the exit code."""
    parser = argparse.ArgumentParser(
        description=(
            "Assert per-module coverage >= 90% for the gated set "
            f"({', '.join(sorted(GATED_MODULES))})."
        )
    )
    parser.add_argument(
        "coverage_json",
        nargs="?",
        default="cov.json",
        help="path to coverage.json (default: cov.json)",
    )
    parser.add_argument(
        "--floor",
        type=float,
        default=CODE_FLOOR,
        help="override the coverage floor (default: 90)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="additionally write the markdown table to this file",
    )
    args = parser.parse_args(argv)

    try:
        data: Mapping[str, object] = json.loads(
            Path(args.coverage_json).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"coverage_gate: cannot read {args.coverage_json}: {exc}",
            file=sys.stderr,
        )
        return EXIT_USAGE

    try:
        observed = evaluate(data)
    except TypeError as exc:
        print(f"coverage_gate: malformed coverage.json: {exc}", file=sys.stderr)
        return EXIT_USAGE

    failures = sorted(m for m, p in observed.items() if p < args.floor)
    table = _table(observed, args.floor)
    print(table)
    if args.report is not None:
        Path(args.report).write_text(f"```\n{table}\n```\n", encoding="utf-8")
    if failures:
        print(
            f"coverage_gate: FAIL -- {len(failures)} module(s) below "
            f"{args.floor:.0f}%: {', '.join(failures)}",
            file=sys.stderr,
        )
        return EXIT_GATE_FAILED
    print(f"coverage_gate: PASS ({len(observed)} modules >= {args.floor:.0f}%)")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
