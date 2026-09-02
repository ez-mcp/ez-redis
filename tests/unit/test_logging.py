"""Tests for :mod:`ez_redis.logging` — the JSON-lines stderr logger.

Covers the plan Part F contract: one JSON object per line, stderr only,
level behavior, content-key filtering (values never emitted), allowlist
semantics, idempotent configuration, log-injection defense, and the
package-import cost invariant.
"""

import json
import subprocess
import sys
from collections.abc import Iterator
from typing import Any

import pytest

from ez_redis import logging as ez_logging
from ez_redis.config import ConfigError, read_log_level

# A distinctive marker used to prove secret values never reach stderr.
_SECRET = "redis://user:sup3rs3cret@host"


@pytest.fixture()
def log_level_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Ensure a deterministic logging environment for each test."""
    monkeypatch.delenv("EZ_REDIS_LOG_LEVEL", raising=False)
    yield


def _capture_stderr(capsys: pytest.CaptureFixture[str]) -> str:
    return capsys.readouterr().err


def _records(stderr: str) -> list[dict[str, Any]]:
    """Parse stderr into JSON records; fails on non-JSON lines."""
    return [json.loads(line) for line in stderr.splitlines() if line]


def test_emits_one_json_object_per_line(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    logger = ez_logging.get_logger("test")
    logger.info("event_one")
    logger.info("event_two")
    records = _records(_capture_stderr(capsys))
    assert len(records) == 2
    assert records[0]["event"] == "event_one"
    assert records[1]["event"] == "event_two"


def test_respects_level_env(
    log_level_env: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("EZ_REDIS_LOG_LEVEL", "INFO")
    ez_logging.configure_logging(read_log_level())
    logger = ez_logging.get_logger("test")
    logger.info("visible_info")
    assert len(_records(_capture_stderr(capsys))) == 1


def test_default_level_is_warning(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging()
    logger = ez_logging.get_logger("test")
    logger.info("below_default")
    logger.warning("at_default")
    records = _records(_capture_stderr(capsys))
    assert [r["event"] for r in records] == ["at_default"]


def test_content_fields_dropped(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    logger = ez_logging.get_logger("test")
    logger.info(
        "event",
        content=_SECRET,
        excerpt=_SECRET,
        prompt=_SECRET,
        snippet=_SECRET,
        Content=_SECRET,
        SNIPPET=_SECRET,
    )
    stderr = _capture_stderr(capsys)
    assert _SECRET not in stderr
    record = _records(stderr)[0]
    assert set(record["dropped_keys"]) == {
        "content",
        "excerpt",
        "prompt",
        "snippet",
        "Content",
        "SNIPPET",
    }


def test_unknown_context_keys_dropped(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    logger = ez_logging.get_logger("test")
    logger.info("event", foo="bar", password=_SECRET)
    stderr = _capture_stderr(capsys)
    assert _SECRET not in stderr
    assert "foo" not in _records(stderr)[0]


def test_allowed_context_keys_pass(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    logger = ez_logging.get_logger("test")
    logger.info("event", rule_id="EZR001", path="src/app.py")
    record = _records(_capture_stderr(capsys))[0]
    assert record["rule_id"] == "EZR001"
    assert record["path"] == "src/app.py"


def test_invalid_level_raises(
    log_level_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EZ_REDIS_LOG_LEVEL", "LOOG")
    with pytest.raises(ConfigError) as excinfo:
        read_log_level()
    message = str(excinfo.value)
    assert "EZ_REDIS_LOG_LEVEL" in message
    # SR-5: the supplied value must not be echoed back.
    assert "LOOG" not in message


def test_stdout_untouched(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    logger = ez_logging.get_logger("test")
    logger.info("event", content=_SECRET)
    assert capsys.readouterr().out == ""


def test_timestamps_are_iso_utc(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    ez_logging.get_logger("test").info("event")
    ts = _records(_capture_stderr(capsys))[0]["ts"]
    assert ts.endswith("Z") or "+00:00" in ts


def test_configure_idempotent(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    ez_logging.configure_logging("INFO")
    ez_logging.get_logger("test").info("event")
    assert len(_records(_capture_stderr(capsys))) == 1


def test_newline_in_value_stays_single_line(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    ez_logging.get_logger("test").info("event", path="a\nb: forged entry")
    stderr = _capture_stderr(capsys)
    assert len(stderr.splitlines()) == 1
    assert "forged entry" in _records(stderr)[0]["path"]


def test_no_structlog_import_at_package_import() -> None:
    """INV: importing ez_redis must not pull structlog (hook hot path)."""
    result = subprocess.run(
        [sys.executable, "-c", "import ez_redis, sys; print(sorted(sys.modules))"],
        check=True,
        capture_output=True,
        text=True,
        shell=False,  # fixed argv; plan Part M / Phase 8 pattern
    )
    # Substring match on the repr is robust to interpreter banners that a
    # strict JSON parse would trip over.
    assert "'structlog'" not in result.stdout
    assert "'ez_redis.logging'" not in result.stdout


def test_component_key_always_present(
    log_level_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    ez_logging.configure_logging("INFO")
    ez_logging.get_logger("worker").info("event")
    assert _records(_capture_stderr(capsys))[0]["component"] == "worker"


def test_read_log_level_valid_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for level in ("debug", "INFO", "warning", "Error", "CRITICAL"):
        monkeypatch.setenv("EZ_REDIS_LOG_LEVEL", level)
        assert read_log_level() == level.upper()


def test_read_log_level_unset_defaults_to_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EZ_REDIS_LOG_LEVEL", raising=False)
    assert read_log_level() == "WARNING"
