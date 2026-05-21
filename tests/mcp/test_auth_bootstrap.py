"""Tests for the auth bootstrap.

Order of preference at startup:
  1. SDK-persisted session (Robinhood JSON / TDA encrypted store)
  2. Env-supplied credentials
  3. No-op + helpful log message
"""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from robin_stocks_mcp.auth import (
    _robinhood_pickle_path,
    bootstrap_login,
    try_reuse_robinhood_session,
)
from robin_stocks_mcp.config import Config


def _cfg(**overrides) -> Config:
    base = dict(
        read_only=True,
        auto_login=True,
        rh_username=None,
        rh_password=None,
        rh_mfa_code=None,
        rh_pickle_path=None,
        rh_pickle_name=None,
        tda_encryption_passcode=None,
        gemini_api_key=None,
        gemini_secret_key=None,
        gemini_sandbox=False,
    )
    base.update(overrides)
    return Config(**base)


# ---------------------------------------------------------------------------
# Session-reuse path (the primary, recommended flow)
# ---------------------------------------------------------------------------


def test_try_reuse_returns_false_when_no_session_file(tmp_path) -> None:
    cfg = _cfg(rh_pickle_path=str(tmp_path))
    assert try_reuse_robinhood_session(cfg) is False


def test_try_reuse_loads_session_and_probes_api(tmp_path) -> None:
    cfg = _cfg(rh_pickle_path=str(tmp_path))
    session_path = _robinhood_pickle_path(cfg)
    with open(session_path, "w") as f:
        json.dump(
            {
                "token_type": "Bearer",
                "access_token": "tok-123",
                "refresh_token": "ref-123",
                "device_token": "dev-123",
            },
            f,
        )

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None

    with patch("robin_stocks_mcp.auth.request_get", return_value=fake_response) as probe, \
         patch("robin_stocks_mcp.auth.update_session") as upd, \
         patch("robin_stocks_mcp.auth.set_login_state") as state:
        ok = try_reuse_robinhood_session(cfg)

    assert ok is True
    probe.assert_called_once()
    upd.assert_any_call("Authorization", "Bearer tok-123")
    state.assert_called_once_with(True)


def test_try_reuse_returns_false_on_invalid_token(tmp_path) -> None:
    cfg = _cfg(rh_pickle_path=str(tmp_path))
    session_path = _robinhood_pickle_path(cfg)
    with open(session_path, "w") as f:
        json.dump(
            {
                "token_type": "Bearer",
                "access_token": "expired",
                "refresh_token": "x",
                "device_token": "x",
            },
            f,
        )

    fake_response = MagicMock()
    fake_response.raise_for_status.side_effect = Exception("401 Unauthorized")

    with patch("robin_stocks_mcp.auth.request_get", return_value=fake_response), \
         patch("robin_stocks_mcp.auth.update_session"), \
         patch("robin_stocks_mcp.auth.set_login_state"):
        ok = try_reuse_robinhood_session(cfg)

    assert ok is False


def test_try_reuse_returns_false_on_corrupt_session_file(tmp_path) -> None:
    """A non-JSON or malformed session file must not break the bootstrap."""
    cfg = _cfg(rh_pickle_path=str(tmp_path))
    session_path = _robinhood_pickle_path(cfg)
    with open(session_path, "w") as f:
        f.write("not valid json {")

    with patch("robin_stocks_mcp.auth.request_get") as probe, \
         patch("robin_stocks_mcp.auth.update_session"), \
         patch("robin_stocks_mcp.auth.set_login_state"):
        ok = try_reuse_robinhood_session(cfg)

    assert ok is False
    probe.assert_not_called()


def test_bootstrap_prefers_session_over_env_creds(tmp_path) -> None:
    cfg = _cfg(
        rh_pickle_path=str(tmp_path),
        rh_username="from-env",
        rh_password="from-env",
    )
    with patch(
        "robin_stocks_mcp.auth.try_reuse_robinhood_session", return_value=True
    ) as reuse, patch("robin_stocks.robinhood.login") as rh_login:
        bootstrap_login(cfg)

    reuse.assert_called_once()
    # Env creds must NOT be used when the cached session works.
    rh_login.assert_not_called()


# ---------------------------------------------------------------------------
# Env-fallback path
# ---------------------------------------------------------------------------


def test_bootstrap_falls_back_to_env_creds_when_session_missing() -> None:
    cfg = _cfg(rh_username="u", rh_password="p", rh_mfa_code="123456")
    with patch(
        "robin_stocks_mcp.auth.try_reuse_robinhood_session", return_value=False
    ), patch("robin_stocks.robinhood.login") as rh_login:
        bootstrap_login(cfg)

    rh_login.assert_called_once()
    _, kwargs = rh_login.call_args
    assert kwargs["username"] == "u"
    assert kwargs["password"] == "p"
    assert kwargs["mfa_code"] == "123456"


def test_bootstrap_no_op_when_nothing_configured() -> None:
    cfg = _cfg()
    with patch(
        "robin_stocks_mcp.auth.try_reuse_robinhood_session", return_value=False
    ), patch("robin_stocks.robinhood.login") as rh_login, patch(
        "robin_stocks.tda.login"
    ) as tda_login, patch("robin_stocks.gemini.login") as gem_login:
        bootstrap_login(cfg)

    rh_login.assert_not_called()
    tda_login.assert_not_called()
    gem_login.assert_not_called()


# ---------------------------------------------------------------------------
# TDA + Gemini still env-driven
# ---------------------------------------------------------------------------


def test_bootstrap_tda_when_passcode_set() -> None:
    with patch("robin_stocks_mcp.auth.try_reuse_robinhood_session", return_value=False), \
         patch("robin_stocks.tda.login") as tda_login:
        bootstrap_login(_cfg(tda_encryption_passcode="pp"))
    tda_login.assert_called_once_with("pp")


def test_bootstrap_gemini_sandbox() -> None:
    with patch("robin_stocks_mcp.auth.try_reuse_robinhood_session", return_value=False), \
         patch("robin_stocks.gemini.login") as gem_login, \
         patch("robin_stocks.gemini.use_sand_box_urls") as sandbox:
        bootstrap_login(
            _cfg(gemini_api_key="k", gemini_secret_key="s", gemini_sandbox=True)
        )
    sandbox.assert_called_once_with(True)
    gem_login.assert_called_once_with("k", "s")


def test_bootstrap_skipped_when_auto_login_disabled() -> None:
    with patch("robin_stocks_mcp.auth.try_reuse_robinhood_session") as reuse, \
         patch("robin_stocks.robinhood.login") as rh_login:
        bootstrap_login(_cfg(auto_login=False, rh_username="u", rh_password="p"))
    reuse.assert_not_called()
    rh_login.assert_not_called()


def test_bootstrap_isolated_failures() -> None:
    """A broker failing must not abort the whole bootstrap or block the others."""
    with patch(
        "robin_stocks_mcp.auth.try_reuse_robinhood_session",
        side_effect=Exception("boom"),
    ), patch("robin_stocks.tda.login") as tda_login:
        bootstrap_login(_cfg(tda_encryption_passcode="pp"))  # must not raise
    tda_login.assert_called_once_with("pp")
