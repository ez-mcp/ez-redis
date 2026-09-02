"""JSON-lines logging to stderr for ez-redis.

Contract (parent plan Phase 1, spec §8):
- Output is one JSON object per line, on **stderr only** (INV-3: stdout is
  reserved for protocol output — stdio MCP transport and hook JSON).
- Level comes from ``EZ_REDIS_LOG_LEVEL`` (default ``WARNING``); an invalid
  value fails loudly with :class:`~ez_redis.config.ConfigError` (C7).
- The event field set is fixed: ``ts``, ``level``, ``event``, ``component``
  plus an explicit allowlist of context keys. Anything else is dropped.
- Fields tagged as content (``content``, ``excerpt``, ``prompt``, ``snippet``)
  are **never** emitted (INV-2): their names are recorded in ``dropped_keys``,
  their values are discarded. This makes accidental logging of file text
  structurally impossible rather than a matter of discipline.

Security notes (plan Part M): the filter is an allowlist of permitted keys,
not a blacklist — unknown keys are dropped by default. JSON rendering escapes
embedded newlines, so a hostile value cannot forge a second log line.

Design: stdlib ``logging`` handlers carry a ``structlog.stdlib.ProcessorFormatter``
so stdlib loggers (e.g. ``mcp``) are rendered into the same JSON format, per
the parent plan Part F. The stderr stream is captured at configure time, and
re-configuration replaces the handler set instead of appending (idempotent).

structlog is typed (``py.typed``); this module uses its typed APIs directly
(no ``Any``, no ignore comments) per python instructions §1. ``structlog.get_logger``
itself is untyped, so :func:`get_logger` is the single typed wrapper.
"""

import logging
import sys
from typing import Final, cast

import structlog
from structlog.typing import EventDict

# Keys whose *values* must never reach stderr. Matching is case-insensitive
# so ``Content``/``SNIPPET`` variants are caught too.
CONTENT_KEYS: Final[frozenset[str]] = frozenset(
    {"content", "excerpt", "prompt", "snippet"},
)

# Context keys an event may carry besides the fixed field set. Anything not
# listed here is dropped (allowlist semantics — security doctrine §3).
ALLOWED_CONTEXT_KEYS: Final[frozenset[str]] = frozenset(
    {"repo_root", "tool", "rule_id", "path", "cap"},
)

FIXED_FIELDS: Final[tuple[str, ...]] = ("ts", "level", "event", "component")

# Key under which dropped-key *names* (never values) are reported.
DROPPED_KEYS_FIELD: Final[str] = "dropped_keys"

_DEFAULT_LEVEL: Final[str] = "WARNING"


def _content_and_allowlist_filter(
    _logger: object,
    _method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Drop content-tagged keys, then non-allowlisted keys.

    Runs as the last processor before ``JSONRenderer`` so no earlier
    processor can re-introduce a dropped key. Reports dropped key *names*
    in-band (never values) to avoid a nested log call recursing through the
    processor chain.
    """
    dropped: list[str] = []

    for key in [k for k in event_dict if k.lower() in CONTENT_KEYS]:
        dropped.append(key)
        del event_dict[key]

    for key in [
        k for k in event_dict if k not in FIXED_FIELDS and k not in ALLOWED_CONTEXT_KEYS
    ]:
        del event_dict[key]
        if not key.startswith("_"):
            # structlog-internal keys (e.g. ``_record``) are dropped silently;
            # caller-visible drops are reported by name only (never values).
            dropped.append(key)

    if dropped:
        event_dict[DROPPED_KEYS_FIELD] = dropped
    return event_dict


def configure_logging(level_name: str | None = None) -> None:
    """Configure JSON-lines logging on stderr. Idempotent.

    Args:
        level_name: Validated level name (``DEBUG`` … ``CRITICAL``,
            case-insensitive). ``None`` defaults to ``WARNING``. Callers
            should pass the result of :func:`ez_redis.config.read_log_level`,
            which raises :class:`~ez_redis.config.ConfigError` on invalid
            input (fail loudly — C7, D-P1-11).

    Re-running replaces the root handler set rather than appending to it, so
    repeated configuration never duplicates output.
    """
    level = level_name if level_name is not None else _DEFAULT_LEVEL

    # Idempotency: replace the root handler set instead of appending.
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    # Bind the stream now rather than lazily: a later sys.stderr swap
    # cannot divert output away from the stderr-only contract (INV-3).
    handler.setStream(sys.stderr)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                # Security filters run last before rendering (docstring).
                _content_and_allowlist_filter,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            ],
        ),
    )
    root.addHandler(handler)
    root.setLevel(level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(component: str) -> structlog.stdlib.BoundLogger:
    """Return a bound logger carrying the fixed ``component`` field.

    ``structlog.get_logger`` has an untyped return; this wrapper is the one
    place a ``cast`` is justified (third-party untyped boundary, narrowed
    immediately — python instructions §1).
    """
    return cast(
        "structlog.stdlib.BoundLogger",
        structlog.get_logger(component=component),
    )
