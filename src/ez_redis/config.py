"""Typed configuration readers for ez-redis environment variables.

Contract (parent plan Phase 1):
- ``EZ_REDIS_DISABLE_HOOKS`` — hooks disabled only for the fixed truthy set
  ``{1, true, yes, on}`` (case-insensitive); anything else, including unset,
  empty, and garbage values, means *enabled* (deterministic and testable;
  plan decision D-P1-12).
- ``EZ_REDIS_LOG_LEVEL`` — validated against the standard level names; an
  invalid value raises :class:`ConfigError` **loudly** (C7, D-P1-11). The
  error message names the variable and the valid set but never echoes the
  supplied value (SR-5: a mistyped secret must not surface in errors).
- ``XDG_CACHE_HOME`` — used only when set to an absolute path (XDG Base
  Directory Specification §2); relative/empty values are ignored and fall
  back to ``~/.cache/ez-redis``. No directory is ever created here — the
  caller (Phase 33) owns creation with 0700 permissions.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: Fixed truthy set for ``EZ_REDIS_DISABLE_HOOKS`` (D-P1-12).
_HOOKS_DISABLED_TRUTHY: Final[frozenset[str]] = frozenset(
    {"1", "true", "yes", "on"},
)

#: Cache-directory name under the resolved base directory.
CACHE_DIR_NAME: Final[str] = "ez-redis"

#: Standard logging levels accepted by ``EZ_REDIS_LOG_LEVEL`` (case-insensitive).
_VALID_LEVELS: Final[tuple[str, ...]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)


class ConfigError(Exception):
    """Raised when configuration is invalid; message is actionable (C7)."""


def _env(name: str) -> str | None:
    """Read an environment variable, treating empty as unset."""
    value = os.environ.get(name)
    return value if value else None


def read_log_level() -> str:
    """Return the validated log level name (upper case).

    Raises:
        ConfigError: if ``EZ_REDIS_LOG_LEVEL`` is set to an unrecognized
            level. The message names the variable and the valid set and
            deliberately does not echo the supplied value (SR-5).
    """
    raw = _env("EZ_REDIS_LOG_LEVEL")
    if raw is None:
        return "WARNING"
    upper = raw.strip().upper()
    if upper not in _VALID_LEVELS:
        raise ConfigError(
            "EZ_REDIS_LOG_LEVEL is set to an invalid value; valid levels "
            f"are: {', '.join(_VALID_LEVELS)} (case-insensitive). "
            "Fix the variable and retry."
        )
    return upper


def hooks_disabled() -> bool:
    """Return True iff ``EZ_REDIS_DISABLE_HOOKS`` holds a truthy value.

    Truthy set: ``1/true/yes/on`` (case-insensitive). Unset, empty, and all
    other values mean hooks stay enabled (D-P1-12: fixed set, no surprises).
    """
    raw = _env("EZ_REDIS_DISABLE_HOOKS")
    if raw is None:
        return False
    return raw.strip().lower() in _HOOKS_DISABLED_TRUTHY


def cache_dir() -> Path:
    """Return the ez-redis cache directory path without creating it.

    Resolution order (XDG Base Directory Specification §2):
    1. ``$XDG_CACHE_HOME/ez-redis`` when ``XDG_CACHE_HOME`` is set to an
       absolute, non-empty path.
    2. Otherwise ``~/.cache/ez-redis`` (relative or empty XDG values are
       ignored per the spec).

    Raises:
        ConfigError: if the user home directory cannot be resolved (rare;
            stripped environments). Fails loudly rather than guessing (C7).
    """
    xdg = _env("XDG_CACHE_HOME")
    if xdg is not None:
        candidate = Path(xdg)
        if candidate.is_absolute():
            return candidate / CACHE_DIR_NAME
        # Relative XDG values are non-conformant; ignore and fall back.
    try:
        home = Path.home()
    except RuntimeError as exc:  # pragma: no cover - depends on passwd lookup
        raise ConfigError(
            "Cannot resolve the user home directory (HOME is unset or "
            "unresolvable); unable to determine the cache directory. "
            "Set XDG_CACHE_HOME to an absolute path and retry."
        ) from exc
    return home / ".cache" / CACHE_DIR_NAME


@dataclass(frozen=True, slots=True)
class Config:
    """Aggregated, immutable configuration snapshot."""

    log_level: str
    hooks_disabled: bool
    cache_dir: Path


def load_config() -> Config:
    """Build a frozen :class:`Config` from the environment.

    Raises:
        ConfigError: via :func:`read_log_level` / :func:`cache_dir` on
            invalid input.
    """
    return Config(
        log_level=read_log_level(),
        hooks_disabled=hooks_disabled(),
        cache_dir=cache_dir(),
    )
