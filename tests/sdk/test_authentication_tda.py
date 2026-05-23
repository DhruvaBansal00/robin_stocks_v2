"""TDA authentication tests — JSON + base64 + Fernet flow.

Covers:
- login_first_time writes a JSON file with base64-encoded ciphertext
- ISO timestamps round-trip correctly
- login reads back the JSON, decrypts, and refreshes when needed
- Each refresh branch (60-day, 30-minute, no-op)
- Backward-compat: SESSION_NAME = "tda.json", PICKLE_NAME aliases it
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from robin_stocks.tda import authentication as tda_auth
from robin_stocks.tda import globals as tda_globals


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------


def test_session_name_is_dot_json() -> None:
    """After #1646, the TDA session file MUST end in .json."""
    assert tda_globals.SESSION_NAME == "tda.json"


def test_pickle_name_aliases_session_name_for_backward_compat() -> None:
    assert tda_globals.PICKLE_NAME == tda_globals.SESSION_NAME


# ---------------------------------------------------------------------------
# Fernet roundtrip
# ---------------------------------------------------------------------------


def test_generate_encryption_passcode_returns_fernet_usable_key() -> None:
    """The generated key must work with Fernet — otherwise login would crash."""
    key = tda_auth.generate_encryption_passcode()
    cipher = Fernet(key.encode() if isinstance(key, str) else key)
    roundtrip = cipher.decrypt(cipher.encrypt(b"hello")).decode()
    assert roundtrip == "hello"


# ---------------------------------------------------------------------------
# login_first_time — writes JSON with base64-encoded ciphertext
# ---------------------------------------------------------------------------


def test_login_first_time_writes_json_file(tmp_path, monkeypatch) -> None:
    """The file must be valid JSON (not pickle bytes)."""
    monkeypatch.setattr(
        "robin_stocks.tda.authentication.Path.home", lambda: tmp_path
    )
    monkeypatch.setattr(
        "robin_stocks.tda.authentication.DATA_DIR_NAME", ".tokens"
    )
    passcode = tda_auth.generate_encryption_passcode()
    tda_auth.login_first_time(passcode, "client-1", "auth-tok", "refresh-tok")

    session_file = tmp_path / ".tokens" / "tda.json"
    assert session_file.exists()

    saved = json.loads(session_file.read_text())  # raises if not valid JSON
    assert "authorization_token" in saved
    assert "refresh_token" in saved
    assert "client_id" in saved
    assert "authorization_timestamp" in saved
    assert "refresh_timestamp" in saved


def test_login_first_time_uses_iso_timestamps(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("robin_stocks.tda.authentication.Path.home", lambda: tmp_path)
    monkeypatch.setattr("robin_stocks.tda.authentication.DATA_DIR_NAME", ".tokens")

    passcode = tda_auth.generate_encryption_passcode()
    tda_auth.login_first_time(passcode, "c", "a", "r")

    saved = json.loads((tmp_path / ".tokens" / "tda.json").read_text())
    parsed_auth = datetime.fromisoformat(saved["authorization_timestamp"])
    parsed_refresh = datetime.fromisoformat(saved["refresh_timestamp"])
    # Both timestamps should be within a second of now()
    assert abs((datetime.now() - parsed_auth).total_seconds()) < 5
    assert abs((datetime.now() - parsed_refresh).total_seconds()) < 5


def test_login_first_time_ciphertext_is_base64_decodable(tmp_path, monkeypatch) -> None:
    """The base64 wrapper ensures bytes can survive JSON encoding."""
    import base64

    monkeypatch.setattr("robin_stocks.tda.authentication.Path.home", lambda: tmp_path)
    monkeypatch.setattr("robin_stocks.tda.authentication.DATA_DIR_NAME", ".tokens")

    passcode = tda_auth.generate_encryption_passcode()
    tda_auth.login_first_time(passcode, "client-1", "the-auth-token", "the-refresh-token")

    saved = json.loads((tmp_path / ".tokens" / "tda.json").read_text())
    cipher = Fernet(passcode.encode())

    # Each base64 string should decode and decrypt back to the original
    assert cipher.decrypt(base64.b64decode(saved["authorization_token"])).decode() == "the-auth-token"
    assert cipher.decrypt(base64.b64decode(saved["refresh_token"])).decode() == "the-refresh-token"
    assert cipher.decrypt(base64.b64decode(saved["client_id"])).decode() == "client-1"


def test_login_first_time_accepts_bytes_passcode(tmp_path, monkeypatch) -> None:
    """The passcode arg may be either bytes or str."""
    monkeypatch.setattr("robin_stocks.tda.authentication.Path.home", lambda: tmp_path)
    monkeypatch.setattr("robin_stocks.tda.authentication.DATA_DIR_NAME", ".tokens")

    passcode_str = tda_auth.generate_encryption_passcode()
    passcode_bytes = passcode_str.encode()

    # Should not raise
    tda_auth.login_first_time(passcode_bytes, "c", "a", "r")
    assert (tmp_path / ".tokens" / "tda.json").exists()


# ---------------------------------------------------------------------------
# login — reads JSON, decrypts, and follows refresh branches
# ---------------------------------------------------------------------------


def _seed_tda_session(tmp_path, monkeypatch, *,
                       authorization_age=timedelta(seconds=0),
                       refresh_age=timedelta(seconds=0)) -> str:
    """Helper: write a TDA session file with controllable timestamps. Returns the passcode."""
    monkeypatch.setattr("robin_stocks.tda.authentication.Path.home", lambda: tmp_path)
    monkeypatch.setattr("robin_stocks.tda.authentication.DATA_DIR_NAME", ".tokens")
    passcode = tda_auth.generate_encryption_passcode()
    tda_auth.login_first_time(passcode, "client-1", "auth-tok", "refresh-tok")

    # Rewrite the timestamps to simulate elapsed time
    path = tmp_path / ".tokens" / "tda.json"
    saved = json.loads(path.read_text())
    now = datetime.now()
    saved["authorization_timestamp"] = (now - authorization_age).isoformat()
    saved["refresh_timestamp"] = (now - refresh_age).isoformat()
    path.write_text(json.dumps(saved))
    return passcode


def test_login_reads_session_and_no_refresh_when_recent(tmp_path, monkeypatch) -> None:
    passcode = _seed_tda_session(tmp_path, monkeypatch)

    with patch("robin_stocks.tda.authentication.request_data") as rd, \
         patch("robin_stocks.tda.authentication.update_session") as upd, \
         patch("robin_stocks.tda.authentication.set_login_state") as state:
        token = tda_auth.login(passcode)

    # No network call, since neither delta was exceeded
    rd.assert_not_called()
    assert token == "Bearer auth-tok"
    upd.assert_any_call("Authorization", "Bearer auth-tok")
    upd.assert_any_call("apikey", "client-1")
    state.assert_called_with(True)


def test_login_authorization_refresh_when_over_30_minutes(tmp_path, monkeypatch) -> None:
    passcode = _seed_tda_session(
        tmp_path, monkeypatch,
        authorization_age=timedelta(minutes=45),  # exceeds 30-min window
        refresh_age=timedelta(days=1),
    )

    new_data = {"access_token": "new-auth-tok"}

    with patch("robin_stocks.tda.authentication.request_data", return_value=(new_data, None)) as rd, \
         patch("robin_stocks.tda.authentication.update_session"), \
         patch("robin_stocks.tda.authentication.set_login_state"):
        token = tda_auth.login(passcode)

    rd.assert_called_once()  # we DID request a new auth token
    assert token == "Bearer new-auth-tok"

    # The on-disk file should have been re-written with the new ciphertext
    saved = json.loads((tmp_path / ".tokens" / "tda.json").read_text())
    cipher = Fernet(passcode.encode())
    import base64
    assert cipher.decrypt(base64.b64decode(saved["authorization_token"])).decode() == "new-auth-tok"


def test_login_full_refresh_when_over_60_days(tmp_path, monkeypatch) -> None:
    """When the refresh token itself is stale, both tokens are rotated."""
    passcode = _seed_tda_session(
        tmp_path, monkeypatch,
        authorization_age=timedelta(days=61),
        refresh_age=timedelta(days=61),
    )

    new_data = {"access_token": "rotated-auth", "refresh_token": "rotated-refresh"}

    with patch("robin_stocks.tda.authentication.request_data", return_value=(new_data, None)), \
         patch("robin_stocks.tda.authentication.update_session"), \
         patch("robin_stocks.tda.authentication.set_login_state"):
        token = tda_auth.login(passcode)

    assert token == "Bearer rotated-auth"

    saved = json.loads((tmp_path / ".tokens" / "tda.json").read_text())
    cipher = Fernet(passcode.encode())
    import base64
    assert cipher.decrypt(base64.b64decode(saved["refresh_token"])).decode() == "rotated-refresh"


def test_login_raises_when_session_file_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("robin_stocks.tda.authentication.Path.home", lambda: tmp_path)
    monkeypatch.setattr("robin_stocks.tda.authentication.DATA_DIR_NAME", ".tokens-empty")

    # Fernet validates the key shape before the file check, so we need a valid key
    with pytest.raises(FileExistsError):
        tda_auth.login(tda_auth.generate_encryption_passcode())


def test_login_raises_when_refresh_returns_no_tokens(tmp_path, monkeypatch) -> None:
    """If the API doesn't return new tokens after a 60-day refresh, login must abort."""
    passcode = _seed_tda_session(
        tmp_path, monkeypatch,
        authorization_age=timedelta(days=61),
        refresh_age=timedelta(days=61),
    )

    # API responds without access_token or refresh_token
    with patch("robin_stocks.tda.authentication.request_data", return_value=({}, None)):
        with pytest.raises(ValueError, match="Refresh token is no longer valid"):
            tda_auth.login(passcode)


def test_login_raises_when_short_refresh_returns_no_token(tmp_path, monkeypatch) -> None:
    """30-minute refresh branch must also raise when API replies empty."""
    passcode = _seed_tda_session(
        tmp_path, monkeypatch,
        authorization_age=timedelta(minutes=45),
        refresh_age=timedelta(days=1),
    )

    with patch("robin_stocks.tda.authentication.request_data", return_value=({}, None)):
        with pytest.raises(ValueError, match="Refresh token is no longer valid"):
            tda_auth.login(passcode)


# ---------------------------------------------------------------------------
# Roundtrip: first_time + login produces the right access token
# ---------------------------------------------------------------------------


def test_login_roundtrip_no_refresh_required(tmp_path, monkeypatch) -> None:
    """End-to-end: write a session, then read it back and confirm the token decrypts."""
    monkeypatch.setattr("robin_stocks.tda.authentication.Path.home", lambda: tmp_path)
    monkeypatch.setattr("robin_stocks.tda.authentication.DATA_DIR_NAME", ".tokens")

    passcode = tda_auth.generate_encryption_passcode()
    tda_auth.login_first_time(passcode, "C-1", "AUTH-TOK", "REFRESH-TOK")

    with patch("robin_stocks.tda.authentication.request_data") as rd, \
         patch("robin_stocks.tda.authentication.update_session"), \
         patch("robin_stocks.tda.authentication.set_login_state"):
        token = tda_auth.login(passcode)

    rd.assert_not_called()
    assert token == "Bearer AUTH-TOK"
