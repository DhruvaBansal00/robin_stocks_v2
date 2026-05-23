"""Robinhood authentication tests — login flow with mocked network.

Covers:
- store_session=True writes a JSON file (#1646)
- store_session=False does NOT write to disk and DOES return data (#1643)
- Failed login (request_post returns None) returns None
- Existing JSON session is read and probe-validated
- Corrupt JSON falls through to a fresh login
- pickle_path / pickle_name override the default directory
"""

from __future__ import annotations

import json
import pickle
from unittest.mock import MagicMock, patch

import pytest

from robin_stocks.robinhood import authentication as auth


@pytest.fixture
def fake_login_data():
    return {
        "token_type": "Bearer",
        "access_token": "access-XYZ",
        "refresh_token": "refresh-XYZ",
        "expires_in": 86400,
        "scope": "internal",
    }


# ---------------------------------------------------------------------------
# store_session=True writes JSON (#1646) and returns data (#1643)
# ---------------------------------------------------------------------------


def test_login_store_session_true_writes_json_file(tmp_path, fake_login_data) -> None:
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        result = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=True,
            pickle_path=str(tmp_path),
        )

    creds_file = tmp_path / "robinhood.json"
    assert creds_file.exists(), "JSON session file should be written"

    # Confirm it's JSON, not pickle, and contains the expected keys
    saved = json.loads(creds_file.read_text())
    assert saved["access_token"] == "access-XYZ"
    assert saved["refresh_token"] == "refresh-XYZ"
    assert saved["token_type"] == "Bearer"
    assert "device_token" in saved

    # And login still returns the data dict
    assert result == fake_login_data


def test_login_uses_dot_json_extension_not_dot_pickle(tmp_path, fake_login_data) -> None:
    """Regression: the old behavior would create robinhood.pickle. After
    #1646 the file MUST end in .json."""
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        auth.login(username="u", password="p", mfa_code="123", store_session=True, pickle_path=str(tmp_path))

    assert (tmp_path / "robinhood.json").exists()
    assert not (tmp_path / "robinhood.pickle").exists()


def test_login_pickle_name_affects_filename(tmp_path, fake_login_data) -> None:
    """pickle_name is the suffix between 'robinhood' and '.json'."""
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        auth.login(
            username="u", password="p", mfa_code="123", store_session=True, pickle_path=str(tmp_path), pickle_name="_test"
        )

    assert (tmp_path / "robinhood_test.json").exists()


# ---------------------------------------------------------------------------
# store_session=False MUST NOT write to disk and MUST return data (#1643)
# ---------------------------------------------------------------------------


def test_login_store_session_false_does_not_write_to_disk(tmp_path, fake_login_data) -> None:
    """Regression test for the indent fix in PR #1643."""
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        result = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=False,
            pickle_path=str(tmp_path),
        )

    # No session file written
    assert not (tmp_path / "robinhood.json").exists()
    # Critically: data must still be returned (the #1643 bug returned None)
    assert result == fake_login_data


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_login_returns_none_on_failed_request(tmp_path) -> None:
    """When request_post returns falsy, login prints failure and returns None."""
    with patch("robin_stocks.robinhood.authentication.request_post", return_value=None):
        result = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=False,
            pickle_path=str(tmp_path),
        )
    assert result is None


def test_login_returns_none_on_empty_response(tmp_path) -> None:
    with patch("robin_stocks.robinhood.authentication.request_post", return_value={}):
        result = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=False,
            pickle_path=str(tmp_path),
        )
    # An empty dict is falsy in `if data` so we hit the failure branch
    assert result is None


# ---------------------------------------------------------------------------
# Existing JSON session is loaded (and probe-validated)
# ---------------------------------------------------------------------------


def _seed_session(tmp_path, payload=None):
    creds_file = tmp_path / "robinhood.json"
    payload = payload or {
        "token_type": "Bearer",
        "access_token": "cached-token",
        "refresh_token": "cached-refresh",
        "device_token": "cached-device",
    }
    creds_file.write_text(json.dumps(payload))
    return creds_file


def test_login_reads_existing_json_session_and_validates(tmp_path) -> None:
    _seed_session(tmp_path)

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None

    with (
        patch("robin_stocks.robinhood.authentication.request_get", return_value=fake_response) as rg,
        patch("robin_stocks.robinhood.authentication.update_session") as upd,
        patch("robin_stocks.robinhood.authentication.set_login_state") as state,
        patch("robin_stocks.robinhood.authentication.request_post") as rp,
    ):
        out = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=True,
            pickle_path=str(tmp_path),
        )

    # Probe was sent
    rg.assert_called_once()
    upd.assert_called_with("Authorization", "Bearer cached-token")
    state.assert_called_with(True)
    # No fresh login over the network was attempted
    rp.assert_not_called()
    # Returned object should reference the cached creds
    assert out["access_token"] == "cached-token"
    assert "logged in using authentication" in out["detail"]


def test_login_falls_back_when_existing_session_token_rejected(tmp_path, fake_login_data) -> None:
    """If the probe raises, login should fall through to a fresh request_post."""
    _seed_session(tmp_path)

    bad_response = MagicMock()
    bad_response.raise_for_status.side_effect = Exception("401 unauthorized")

    with (
        patch("robin_stocks.robinhood.authentication.request_get", return_value=bad_response),
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data) as rp,
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        out = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=True,
            pickle_path=str(tmp_path),
        )

    rp.assert_called_once()  # we did fall through to a new login
    assert out["access_token"] == "access-XYZ"


def test_login_corrupt_json_session_falls_back_gracefully(tmp_path, fake_login_data) -> None:
    """A non-JSON / malformed session file must not crash login()."""
    (tmp_path / "robinhood.json").write_text("not json {{{")

    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        out = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=True,
            pickle_path=str(tmp_path),
        )

    assert out == fake_login_data


def test_login_legacy_pickle_session_file_is_ignored_after_migration(tmp_path, fake_login_data) -> None:
    """The post-#1646 code looks for robinhood.json. A leftover robinhood.pickle
    in the same dir must be ignored — never deserialized."""
    legacy = tmp_path / "robinhood.pickle"
    with open(legacy, "wb") as f:
        pickle.dump({"will": "never load"}, f)

    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        out = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=True,
            pickle_path=str(tmp_path),
        )

    # We did a fresh login (the .pickle was untouched on the load path)
    assert out == fake_login_data
    # And a new .json was written
    assert (tmp_path / "robinhood.json").exists()


def test_login_store_session_false_with_existing_file_removes_it(tmp_path, fake_login_data) -> None:
    """The code explicitly removes the session file when store_session=False."""
    _seed_session(tmp_path)
    assert (tmp_path / "robinhood.json").exists()

    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        out = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=False,
            pickle_path=str(tmp_path),
        )

    assert not (tmp_path / "robinhood.json").exists()
    assert out == fake_login_data


# ---------------------------------------------------------------------------
# generate_device_token — must produce a stable, structured token
# ---------------------------------------------------------------------------


def test_generate_device_token_format() -> None:
    """Device tokens are 8-4-4-4-12 hex strings (UUIDv4-like layout)."""
    token = auth.generate_device_token()
    parts = token.split("-")
    assert len(parts) == 5
    assert [len(p) for p in parts] == [8, 4, 4, 4, 12]
    # All hex
    int(token.replace("-", ""), 16)


def test_generate_device_token_is_pseudo_unique() -> None:
    """Two consecutive calls must produce different tokens."""
    a = auth.generate_device_token()
    b = auth.generate_device_token()
    assert a != b


# ---------------------------------------------------------------------------
# logout — clears session state
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# pickle_path branches
# ---------------------------------------------------------------------------


def test_login_pickle_path_relative_normalized_to_cwd(tmp_path, fake_login_data, monkeypatch) -> None:
    """A relative pickle_path is resolved against cwd via normpath."""
    monkeypatch.chdir(tmp_path)
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        auth.login(username="u", password="p", mfa_code="123", store_session=True, pickle_path="relsubdir")
    assert (tmp_path / "relsubdir" / "robinhood.json").exists()


def test_login_creates_data_dir_if_missing(tmp_path, fake_login_data) -> None:
    """The .tokens dir is created when it doesn't already exist."""
    sub = tmp_path / "fresh"
    assert not sub.exists()
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        auth.login(username="u", password="p", mfa_code="123", store_session=True, pickle_path=str(sub))
    assert sub.exists()


# ---------------------------------------------------------------------------
# Verification workflow branch (#1643/2)
# ---------------------------------------------------------------------------


def test_login_triggers_verification_workflow_when_present(tmp_path) -> None:
    """When the first response contains 'verification_workflow', _validate_sherrif_id
    is called and a second request_post is made to retry the login."""
    challenge_response = {"verification_workflow": {"id": "workflow-1"}}
    success_response = {
        "access_token": "tok",
        "token_type": "Bearer",
        "refresh_token": "ref",
    }
    with (
        patch(
            "robin_stocks.robinhood.authentication.request_post",
            side_effect=[challenge_response, success_response],
        ) as rp,
        patch("robin_stocks.robinhood.authentication._validate_sherrif_id") as validate,
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
    ):
        out = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=False,
            pickle_path=str(tmp_path),
        )

    validate.assert_called_once()
    assert rp.call_count == 2
    assert out["access_token"] == "tok"


def test_login_prompts_when_username_missing(tmp_path, fake_login_data) -> None:
    """If username is None, login() prompts via input()."""
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
        patch("builtins.input", return_value="prompted-user") as inp,
    ):
        auth.login(password="p", mfa_code="123", store_session=False, pickle_path=str(tmp_path))
    inp.assert_called_once()


def test_login_prompts_when_password_missing(tmp_path, fake_login_data) -> None:
    """If password is None, login() uses getpass()."""
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=fake_login_data),
        patch("robin_stocks.robinhood.authentication.update_session"),
        patch("robin_stocks.robinhood.authentication.set_login_state"),
        patch("robin_stocks.robinhood.authentication.getpass.getpass", return_value="prompted-pw") as gp,
    ):
        auth.login(username="u", mfa_code="123", store_session=False, pickle_path=str(tmp_path))
    gp.assert_called_once()


def test_login_swallows_exception_during_verification(tmp_path) -> None:
    """If something inside the success-handling try block raises, login()
    catches it and prints, rather than propagating."""
    bad_data = {"access_token": "tok", "token_type": "Bearer", "refresh_token": "ref"}
    with (
        patch("robin_stocks.robinhood.authentication.request_post", return_value=bad_data),
        patch(
            "robin_stocks.robinhood.authentication.update_session",
            side_effect=Exception("kaboom"),
        ),
    ):
        # Should not raise
        out = auth.login(
            username="u",
            password="p",
            mfa_code="123",
            store_session=False,
            pickle_path=str(tmp_path),
        )
    # On exception inside the try block, login falls through to "Login failed" path
    # and returns None
    assert out is None


# ---------------------------------------------------------------------------
# _get_sherrif_id helper
# ---------------------------------------------------------------------------


def test_get_sherrif_id_returns_id() -> None:
    assert auth._get_sherrif_id({"id": "verify-1"}) == "verify-1"


def test_get_sherrif_id_raises_when_no_id() -> None:
    with pytest.raises(Exception, match="No verification ID"):
        auth._get_sherrif_id({"foo": "bar"})


def test_logout_clears_state() -> None:
    # The login_required decorator reads LOGGED_IN from helper.py's module
    # namespace, not authentication.py's
    with (
        patch("robin_stocks.robinhood.helper.LOGGED_IN", True),
        patch("robin_stocks.robinhood.authentication.set_login_state") as state,
        patch("robin_stocks.robinhood.authentication.update_session") as upd,
    ):
        auth.logout()
    state.assert_called_with(False)
    upd.assert_called_with("Authorization", None)
