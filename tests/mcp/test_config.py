"""Tests for env-var driven configuration."""

from __future__ import annotations

import importlib

import pytest

from robin_stocks_mcp import config as config_mod


def reload_config(monkeypatch: pytest.MonkeyPatch, **env: str) -> config_mod.Config:
    for k in list(env.keys()):
        monkeypatch.setenv(k, env[k])
    importlib.reload(config_mod)
    return config_mod.load_config()


def test_read_only_default_is_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROBIN_STOCKS_MCP_READ_ONLY", raising=False)
    cfg = config_mod.load_config()
    assert cfg.read_only is True


@pytest.mark.parametrize("val,expected", [
    ("true", True),
    ("1", True),
    ("yes", True),
    ("y", True),
    ("on", True),
    ("no", False),
    ("0", False),
    ("false", False),
    ("off", False),
])
def test_bool_env_parser(monkeypatch: pytest.MonkeyPatch, val: str, expected: bool) -> None:
    # Use a different env var to test the helper directly
    monkeypatch.setenv("ROBIN_STOCKS_MCP_AUTO_LOGIN", val)
    cfg = config_mod.load_config()
    assert cfg.auto_login is expected


def test_credentials_propagate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROBINHOOD_USERNAME", "user")
    monkeypatch.setenv("ROBINHOOD_PASSWORD", "pass")
    monkeypatch.setenv("TDA_ENCRYPTION_PASSCODE", "pass-code")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_SECRET_KEY", "s")
    cfg = config_mod.load_config()
    assert cfg.rh_username == "user"
    assert cfg.rh_password == "pass"
    assert cfg.tda_encryption_passcode == "pass-code"
    assert cfg.gemini_api_key == "k"
    assert cfg.gemini_secret_key == "s"


def test_rh_alias_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROBINHOOD_USERNAME", raising=False)
    monkeypatch.delenv("ROBINHOOD_PASSWORD", raising=False)
    monkeypatch.setenv("RH_USERNAME", "alt")
    monkeypatch.setenv("RH_PASSWORD", "altpass")
    cfg = config_mod.load_config()
    assert cfg.rh_username == "alt"
    assert cfg.rh_password == "altpass"
