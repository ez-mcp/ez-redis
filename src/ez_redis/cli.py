"""Fail-loud console-script stub (Phase 1; the real CLI ships in Phase 5)."""

import sys

print(
    "ez-redis CLI ships in Phase 5; this install exposes the entry point only.",
    file=sys.stderr,
)
raise SystemExit(2)
