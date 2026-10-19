# EZ-Redis

Redis expertise for AI coding agents: static analysis of application
Redis usage. `ez-redis` parses application source code, extracts Redis
commands, keys, and invalidation edges into a typed intermediate
representation, and reports expert diagnoses.

## Setup

Requires Python >= 3.11 and [uv](https://docs.astral.sh/uv/).

```console
$ uv sync --locked
```

## Test

```console
$ uv run ruff check . && uv run ruff format --check .
$ uv run pyright
$ uv run pytest -m unit
$ uv run pytest -m golden
$ uv run pytest -m property
```

Known-good full check: `uv run python scripts/dod_check.py`.

## Plans

- [`PLAN.MD`](PLAN.MD) -- overall project plan ("PLAN-MOTHER").
- [`PLAN-PHASES-1-2.md`](PLAN-PHASES-1-2.md) -- execution plan for Phases 1-2
  (this repo state implements its scaffold; packaging: §4.5, CI: §6.5,
  Definition of Done: §8, work packages: §10).