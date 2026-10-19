#!/usr/bin/env python3
"""Golden-diff classifier (plan sections 6.1 and 6.5, job 5 diagnostic).

Reads a unified diff of ``tests/golden/`` (from stdin or a file argument) and
attributes each changed hunk (its ``+`` lines) to its top-level JSON key (the
first ``  "key":`` line among the hunk's added lines claims the hunk).
Classification (plan 6.1: "Diff becomes diagnosable"):

- all hunks attribute to ``grammar_versions`` only ->
  ``expected: language bump PR -- regenerate with --update-goldens and say why``
  (exit 0);
- anything else -> ``explain in PR body under why-goldens:`` (exit 1).

Complexity: linear in diff length, O(1) state per hunk.

Usage (CI diagnostic, plan 6.5 job 2)::

    git diff <base> HEAD -- tests/golden/ | uv run python scripts/golden_classify.py

Exit codes: 0 = grammar_versions-only, 1 = change needs explanation, 2 =
usage/parse error. Pure stdlib.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Final

# First top-level key seen in the added lines of a hunk, e.g. '  "op":'.
KEY_PATCH: Final[re.Pattern[str]] = re.compile(
    r'^\+\s{2}"([A-Za-z_][A-Za-z0-9_]*)"\s*:'
)

HUNK_HEADER: Final[re.Pattern[str]] = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")

EXIT_GRAMMAR_ONLY: Final[int] = 0
EXIT_NEEDS_EXPLANATION: Final[int] = 1
EXIT_USAGE: Final[int] = 2


def attribute(diff_text: str) -> dict[str, list[int]]:
    """Map each top-level JSON key to the hunk numbers attributed to it.

    Linear single pass over the diff; a hunk ends at the next ``@@`` line
    (or EOF); its attribution is the first ``  "key":`` among its ``+`` lines.
    Hunk numbers are 1-based ordinals of appearance, matching ``git diff -U3``
    output order.
    """
    attributed: dict[str, list[int]] = {}
    hunk_no = 0
    in_hunk = False
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            match = HUNK_HEADER.match(line)
            if match is None:
                # Non-standard header: stop attributing rather than guess.
                in_hunk = False
                continue
            hunk_no += 1
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith(("---", "+++")) or line.startswith((" ", "-")):
            continue
        if line.startswith("+"):
            match = KEY_PATCH.match(line)
            if match is not None:
                key = match.group(1)
                attributed.setdefault(key, []).append(hunk_no)
                in_hunk = False  # first top-level key claims the hunk
                continue
    return attributed


def classify(attributed: dict[str, list[int]]) -> tuple[str, int]:
    """Classify attributed hunks into (message, exit_code)."""
    if not attributed:
        return (
            "golden_classify: no top-level JSON keys found in added lines; "
            "explain in PR body under why-goldens: (or the diff is not a "
            "golden JSON diff)",
            EXIT_NEEDS_EXPLANATION,
        )
    keys = sorted(attributed)
    if keys == ["grammar_versions"]:
        return (
            "expected: language bump PR -- regenerate with --update-goldens "
            "and say why",
            EXIT_GRAMMAR_ONLY,
        )
    return (
        f"keys {keys} changed: explain in PR body under why-goldens:",
        EXIT_NEEDS_EXPLANATION,
    )


def main() -> int:
    """Read the diff, classify it, print, and exit per the classification."""
    if len(sys.argv) > 2:
        print("usage: golden_classify.py [diff-file]", file=sys.stderr)
        return EXIT_USAGE
    if len(sys.argv) == 2:
        path = sys.argv[1]
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"golden_classify: cannot read {path}: {exc}", file=sys.stderr)
            return EXIT_USAGE
    else:
        text = sys.stdin.read()
    attributed = attribute(text)
    message, exit_code = classify(attributed)
    print(f"golden_classify: {message}")
    if attributed:
        for key in sorted(attributed):
            hunks = ", ".join(map(str, attributed[key]))
            print(f"  {key}: hunk(s) {hunks}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
