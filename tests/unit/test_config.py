"""Tests for :mod:`ez_redis.config` — typed environment readers.

Covers the plan Part H contract: truthy-set semantics for the hooks flag,
loud validation of the log level (never echoing the value, SR-5), XDG
fallback rules with no disk writes, and frozen configuration snapshots.
"""

import io
from contextlib import redirect_stdout, suppress
from pathlib import Path
from unittest.mock import patch

import pytest

from ez_redis.config import (
    ConfigError,
    cache_dir,
    hooks_disabled,
    load_config,
    read_log_level,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("EZ_REDIS_DISABLE_HOOKS", "EZ_REDIS_LOG_LEVEL", "XDG_CACHE_HOME"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", "Yes", "ON"])
def test_hooks_disabled_truthy_set(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_REDIS_DISABLE_HOOKS", value)
    assert hooks_disabled() is True


@pytest.mark.parametrize("value", ["", "0", "false", "off", "banana", "  ", "enabled"])
def test_hooks_disabled_falsy_and_garbage(
    value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EZ_REDIS_DISABLE_HOOKS", value)
    assert hooks_disabled() is False


def test_hooks_disabled_unset() -> None:
    assert hooks_disabled() is False


def test_log_level_valid_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_REDIS_LOG_LEVEL", "info")
    assert read_log_level() == "INFO"


def test_log_level_invalid_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_REDIS_LOG_LEVEL", "LOOG")
    with pytest.raises(ConfigError) as excinfo:
        read_log_level()
    message = str(excinfo.value)
    assert "EZ_REDIS_LOG_LEVEL" in message
    assert "DEBUG" in message and "CRITICAL" in message  # valid set named
    assert "LOOG" not in message  # SR-5: value never echoed


def test_cache_dir_xdg_absolute(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    xdg = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(xdg))
    assert cache_dir() == xdg / "ez-redis"


def test_cache_dir_xdg_relative_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", "relative/path")
    assert cache_dir() == Path.home() / ".cache" / "ez-redis"


def test_cache_dir_xdg_empty_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", "")
    assert cache_dir() == Path.home() / ".cache" / "ez-redis"


def test_cache_dir_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    assert cache_dir() == Path.home() / ".cache" / "ez-redis"


def test_cache_dir_never_creates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    xdg = tmp_path / "never-created"
    monkeypatch.setenv("XDG_CACHE_HOME", str(xdg))
    cache_dir()
    assert not xdg.exists()


def test_cache_dir_no_disk_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Phase 33 owns directory creation; config must never mkdir."""
    with patch.object(Path, "mkdir", side_effect=AssertionError("mkdir called")):
        cache_dir()


def test_load_config_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_REDIS_LOG_LEVEL", "INFO")
    config = load_config()
    with pytest.raises(AttributeError):
        config.log_level = "DEBUG"  # type: ignore[misc] # frozen-dataclass probe


def test_config_error_message_actionable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Error path writes nothing to stdout and names the offending variable."""
    monkeypatch.setenv("EZ_REDIS_LOG_LEVEL", "BAD-VALUE-XYZ")
    with pytest.raises(ConfigError) as excinfo:
        read_log_level()
    assert "EZ_REDIS_LOG_LEVEL" in str(excinfo.value)
    assert "BAD-VALUE-XYZ" not in str(excinfo.value)
    buffer = io.StringIO()
    with redirect_stdout(buffer), suppress(ConfigError):
        read_log_level()
    assert buffer.getvalue() == ""
