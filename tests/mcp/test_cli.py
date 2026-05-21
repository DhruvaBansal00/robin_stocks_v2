"""Tests for the `robin-stocks-mcp` CLI subcommands (login, tda-setup, logout)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks_mcp.server import main


def test_default_command_is_serve(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bare `robin-stocks-mcp` (no subcommand) should default to serve."""
    with patch("robin_stocks_mcp.server._cmd_serve", return_value=0) as serve, \
         patch("robin_stocks_mcp.server.bootstrap_login"):
        rc = main([])
    serve.assert_called_once()
    assert rc == 0


def test_legacy_transport_flag_still_works() -> None:
    """`robin-stocks-mcp --transport stdio` (old form) still routes to serve."""
    with patch("robin_stocks_mcp.server._cmd_serve", return_value=0) as serve:
        main(["--transport", "stdio"])
    serve.assert_called_once()
    args = serve.call_args[0][0]
    assert args.transport == "stdio"


def test_login_subcommand_calls_rh_login() -> None:
    with patch("robin_stocks.robinhood.login") as rh_login:
        main([
            "login",
            "--username", "u",
            "--password", "p",
            "--mfa-code", "123456",
        ])
    rh_login.assert_called_once()
    _, kwargs = rh_login.call_args
    assert kwargs["username"] == "u"
    assert kwargs["password"] == "p"
    assert kwargs["mfa_code"] == "123456"
    assert kwargs["store_session"] is True


def test_tda_setup_calls_login_first_time() -> None:
    with patch("robin_stocks.tda.login_first_time") as setup:
        main([
            "tda-setup",
            "--passcode", "pp",
            "--client-id", "cid",
            "--auth-token", "auth",
            "--refresh-token", "ref",
        ])
    setup.assert_called_once_with("pp", "cid", "auth", "ref")


def test_tda_setup_generates_passcode_when_flag_given(capsys) -> None:
    with patch("robin_stocks.tda.generate_encryption_passcode", return_value="GEN-PASS"), \
         patch("robin_stocks.tda.login_first_time") as setup:
        main([
            "tda-setup",
            "--generate-passcode",
            "--client-id", "cid",
            "--auth-token", "auth",
            "--refresh-token", "ref",
        ])
    setup.assert_called_once()
    args, _ = setup.call_args
    assert args[0] == "GEN-PASS"
    out = capsys.readouterr().out
    assert "GEN-PASS" in out


def test_logout_clears_both_brokers_by_default() -> None:
    with patch("robin_stocks.robinhood.logout") as rh_out, \
         patch("robin_stocks.gemini.logout") as gem_out:
        main(["logout"])
    rh_out.assert_called_once()
    gem_out.assert_called_once()


def test_logout_can_target_one_broker() -> None:
    with patch("robin_stocks.robinhood.logout") as rh_out, \
         patch("robin_stocks.gemini.logout") as gem_out:
        main(["logout", "rh"])
    rh_out.assert_called_once()
    gem_out.assert_not_called()
