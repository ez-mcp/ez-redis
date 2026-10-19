#!/usr/bin/env python3
"""Executable Definition-of-Done check (plan sections 6.5 and 8).

Runs the Phase-1/2 DoD commands with fixed argv (``shell=False``) and prints
a pass/fail table to stdout and to ``$GITHUB_STEP_SUMMARY`` when set. Exits
non-zero if any item is unmet.

Usage::

    uv run python scripts/dod_check.py

Exit codes: 0 = all DoD items met, 1 = usage error, 2 = at least one unmet.
Pure stdlib.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

EXIT_OK: Final[int] = 0
EXIT_USAGE: Final[int] = 1
EXIT_DOD_FAILED: Final[int] = 2
DEFAULT_TIMEOUT: Final[int] = 900  # seconds per command


@dataclass(frozen=True)
class Item:
    """One DoD row: display name plus the fixed argv to run."""

    name: str
    argv: tuple[str, ...]


def _unit_item() -> Item:
    """Adversarial tests are folded into the unit marker run in Phase 2.

    Phase 1: ``pytest -m unit`` (fast, <15 s). Phase 2 mark the same item with
    ``or adversarial`` once the corpus exists -- keep the table row stable.
    """
    return Item("pytest -m unit", ("uv", "run", "pytest", "-m", "unit"))


DO_D_ITEMS: Final[tuple[Item, ...]] = (
    # NOTE (uv 0.10.9): `uv sync --locked --frozen` is rejected -- the flags
    # became mutually exclusive; `--locked` alone is the drift-failing form.
    Item("uv sync --locked", ("uv", "sync", "--locked")),
    Item("ruff check .", ("uv", "run", "ruff", "check", ".")),
    Item(
        "ruff format --check .",
        ("uv", "run", "ruff", "format", "--check", "."),
    ),
    Item("pyright", ("uv", "run", "pyright")),
    _unit_item(),
    Item("pytest -m golden", ("uv", "run", "pytest", "-m", "golden")),
    Item("pytest -m property", ("uv", "run", "pytest", "-m", "property")),
    Item(
        "pytest --cov (per-module >=90%)",
        (
            "uv",
            "run",
            "pytest",
            "--cov=src/ez_redis",
            "--cov-branch",
            "--cov-report=json:cov.json",
            "-q",
        ),
    ),
    Item(
        "coverage gate (scripts/coverage_gate.py)",
        ("uv", "run", "python", "scripts/coverage_gate.py"),
    ),
)


def _run(item: Item, timeout: int) -> tuple[bool, str]:
    """Run one DoD command; return (passed, first error line or '')."""
    env = dict(os.environ)
    env.setdefault("HYPOTHESIS_PROFILE", "ci")
    env["PYTHONHASHSEED"] = "0"  # determinism aid for property runs
    try:
        proc = subprocess.run(
            item.argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            env=env,
        )
    except FileNotFoundError:
        return False, f"executable not found: {item.argv[0]}"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s"
    if proc.returncode == 0:
        return True, ""
    tail = (proc.stderr or proc.stdout).strip().splitlines()
    return False, tail[-1] if tail else f"exit {proc.returncode}"


def render_table(rows: list[tuple[Item, bool, str]]) -> str:
    """Render the pass/fail table (plain text, no external dependency)."""
    width = max(len(item.name) for item, _, _ in rows)
    lines = [f"{'DoD item':<{width}}  result", "-" * (width + 8)]
    for item, ok, detail in rows:
        status = "PASS" if ok else "FAIL"
        suffix = f"  ({detail})" if detail else ""
        lines.append(f"{item.name:<{width}}  {status}{suffix}")
    return "\n".join(lines)


def render_markdown(rows: list[tuple[Item, bool, str]]) -> str:
    """Render the table as GitHub-flavored markdown for $GITHUB_STEP_SUMMARY."""
    lines = ["| DoD item | result | detail |", "|---|---|---|"]
    for item, ok, detail in rows:
        lines.append(f"| {item.name} | {'yes' if ok else '**NO**'} | {detail or '—'} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run every DoD item, print the table, exit non-zero on any failure."""
    parser = argparse.ArgumentParser(description=__doc__.partition("\n\n")[0])
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        metavar="SECONDS",
        help=f"per-command timeout (default {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="stop at the first failing item",
    )
    args = parser.parse_args(argv)

    rows: list[tuple[Item, bool, str]] = []
    for item in DO_D_ITEMS:
        ok, detail = _run(item, args.timeout)
        rows.append((item, ok, detail))
        if not ok and args.stop_on_fail:
            break

    print(render_table(rows))
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary_file:
            summary_file.write(render_markdown(rows) + "\n")
    failures = [item.name for item, ok, _ in rows if not ok]
    if failures:
        print(f"dod_check: {len(failures)} unmet item(s): {', '.join(failures)}")
        return EXIT_DOD_FAILED
    print("dod_check: all DoD items met")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
