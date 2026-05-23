"""Recurring-investments tests (PR #1633).

Covers:
- ``get_recurring_investments`` URL construction
- ``create_recurring_investment`` payload shape, error branches
- ``update_recurring_investment`` PATCH + Content-Type handling
- ``cancel_recurring_investment`` PATCH with state='deleted'
- ``get_next_investment_date`` default-date behavior
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from robin_stocks.robinhood import recurring_investments as ri


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ---------------------------------------------------------------------------
# get_recurring_investments
# ---------------------------------------------------------------------------


def test_get_recurring_investments_default_calls_paginated() -> None:
    with patch("robin_stocks.robinhood.recurring_investments.request_get", return_value=[{"id": "s1"}]) as rg:
        out = ri.get_recurring_investments()
    # Pagination flag passed
    assert rg.call_args[0][1] == "pagination"
    assert out == [{"id": "s1"}]


def test_get_recurring_investments_with_account_number_targets_url() -> None:
    with patch("robin_stocks.robinhood.recurring_investments.request_get", return_value=[]) as rg:
        ri.get_recurring_investments(account_number="ACC-1")
    url = rg.call_args[0][0]
    assert "account_number=ACC-1" in url


def test_get_recurring_investments_with_asset_types_targets_url() -> None:
    with patch("robin_stocks.robinhood.recurring_investments.request_get", return_value=[]) as rg:
        ri.get_recurring_investments(asset_types=["equity", "crypto"])
    url = rg.call_args[0][0]
    assert "asset_types=equity" in url
    assert "asset_types=crypto" in url


def test_get_recurring_investments_filters_by_info() -> None:
    with patch("robin_stocks.robinhood.recurring_investments.request_get", return_value=[{"id": "s1"}, {"id": "s2"}]):
        out = ri.get_recurring_investments(info="id")
    assert out == ["s1", "s2"]


# ---------------------------------------------------------------------------
# create_recurring_investment
# ---------------------------------------------------------------------------


def _ok_response(body):
    res = MagicMock()
    res.status_code = 200
    res.json.return_value = body
    return res


def _bad_response(status_code, body=None):
    res = MagicMock()
    res.status_code = status_code
    if body is None:
        res.json.side_effect = ValueError("not json")
    else:
        res.json.return_value = body
    return res


def test_create_recurring_investment_happy_path() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=_ok_response({"id": "sched-1"})) as rp,
    ):
        out = ri.create_recurring_investment("AAPL", 5.0, frequency="weekly")

    assert out == {"id": "sched-1"}
    # Verify the payload shape
    payload = rp.call_args[0][1]
    assert payload["account_number"] == "ACC-1"
    assert payload["amount"] == {"amount": "5.0", "currency_code": "USD"}
    assert payload["frequency"] == "weekly"
    assert payload["investment_asset"]["asset_id"] == "inst-1"
    assert payload["investment_asset"]["asset_symbol"] == "AAPL"
    assert payload["investment_asset"]["asset_type"] == "equity"
    assert payload["source_of_funds"] == "buying_power"
    assert "start_date" in payload  # Defaults to today


def test_create_recurring_investment_defaults_start_date_to_today() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=_ok_response({"id": "s1"})) as rp,
    ):
        ri.create_recurring_investment("AAPL", 5.0)
    payload = rp.call_args[0][1]
    assert payload["start_date"] == today


def test_create_recurring_investment_explicit_start_date_honored() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=_ok_response({"id": "s1"})) as rp,
    ):
        ri.create_recurring_investment("AAPL", 5.0, start_date="2026-12-01")
    assert rp.call_args[0][1]["start_date"] == "2026-12-01"


def test_create_recurring_investment_uses_explicit_account_number() -> None:
    """When account_number is passed, load_account_profile must not be called."""
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile") as lap,
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=_ok_response({"id": "s1"})),
    ):
        ri.create_recurring_investment("AAPL", 5.0, account_number="manual-acct")
    lap.assert_not_called()


def test_create_recurring_investment_returns_none_when_account_lookup_fails() -> None:
    with patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={}):
        # account_data doesn't have 'account_number' → result is None
        out = ri.create_recurring_investment("AAPL", 5.0)
    assert out is None


def test_create_recurring_investment_returns_none_when_symbol_unknown() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=None),
    ):
        out = ri.create_recurring_investment("UNKNOWN", 5.0)
    assert out is None


def test_create_recurring_investment_returns_none_when_instrument_lacks_id() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"name": "foo"}]),
    ):
        out = ri.create_recurring_investment("AAPL", 5.0)
    assert out is None


def test_create_recurring_investment_returns_none_on_request_failure() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=None),
    ):
        out = ri.create_recurring_investment("AAPL", 5.0)
    assert out is None


def test_create_recurring_investment_returns_none_on_400_response() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch(
            "robin_stocks.robinhood.recurring_investments.request_post",
            return_value=_bad_response(400, {"detail": "bad amount"}),
        ),
    ):
        assert ri.create_recurring_investment("AAPL", 0.5) is None


def test_create_recurring_investment_handles_non_json_error_body() -> None:
    """If the error response can't be parsed as JSON, we still return None."""
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch(
            "robin_stocks.robinhood.recurring_investments.request_post",
            return_value=_bad_response(500),  # .json() raises
        ),
    ):
        assert ri.create_recurring_investment("AAPL", 5.0) is None


def test_create_recurring_investment_uppercases_symbol_in_payload() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
        patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=_ok_response({"id": "s1"})) as rp,
    ):
        ri.create_recurring_investment("aapl", 5.0)
    assert rp.call_args[0][1]["investment_asset"]["asset_symbol"] == "AAPL"


def test_create_recurring_investment_201_response_treated_as_success() -> None:
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
    ):
        resp = MagicMock(status_code=201)
        resp.json.return_value = {"id": "created"}
        with patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=resp):
            out = ri.create_recurring_investment("AAPL", 5.0)
    assert out == {"id": "created"}


def test_create_recurring_investment_handles_dict_error_message() -> None:
    """Some Robinhood error responses put a dict in `detail`; we must stringify it."""
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
    ):
        resp = MagicMock(status_code=400)
        resp.json.return_value = {"detail": {"field": "amount", "code": "too_low"}}
        with patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=resp):
            out = ri.create_recurring_investment("AAPL", 0.5)
    assert out is None


def test_create_recurring_investment_returns_none_on_unparseable_success_body() -> None:
    """A 200 OK with a non-JSON body must not crash; just return None."""
    with (
        patch("robin_stocks.robinhood.recurring_investments.load_account_profile", return_value={"account_number": "ACC-1"}),
        patch("robin_stocks.robinhood.recurring_investments.get_instruments_by_symbols", return_value=[{"id": "inst-1"}]),
    ):
        resp = MagicMock(status_code=200)
        resp.json.side_effect = ValueError("not JSON")
        with patch("robin_stocks.robinhood.recurring_investments.request_post", return_value=resp):
            out = ri.create_recurring_investment("AAPL", 5.0)
    assert out is None


# ---------------------------------------------------------------------------
# update_recurring_investment
# ---------------------------------------------------------------------------


def test_update_recurring_investment_builds_correct_patch_payload() -> None:
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "paused"}

    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.update_recurring_investment("sched-1", account_number="ACC-1", state="paused", amount=10.0)

    # Verify PATCH was called with the right URL + JSON body
    args, kwargs = mock_session.patch.call_args
    assert "sched-1" in args[0]
    body = kwargs["json"]
    assert body["state"] == "paused"
    assert body["amount"] == {"amount": "10.0", "currency_code": "USD"}
    assert out == {"state": "paused"}


def test_update_recurring_investment_restores_content_type_after_patch() -> None:
    """Critical: Content-Type was temporarily set to application/json. It MUST
    be restored to the original so subsequent requests don't break."""
    resp = MagicMock(status_code=200, json=lambda: {})
    mock_session = MagicMock()
    original = "application/x-www-form-urlencoded; charset=utf-8"
    mock_session.headers = {"Content-Type": original}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        ri.update_recurring_investment("s1", account_number="ACC", state="active")

    assert mock_session.headers["Content-Type"] == original


def test_update_recurring_investment_returns_none_on_400() -> None:
    resp = MagicMock(status_code=400)
    resp.json.return_value = {"detail": "bad"}
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.update_recurring_investment("s1", account_number="ACC", state="paused")
    assert out is None


def test_update_recurring_investment_returns_none_on_exception() -> None:
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.side_effect = Exception("boom")

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.update_recurring_investment("s1", account_number="ACC", state="paused")
    assert out is None


def test_update_recurring_investment_returns_none_without_fields() -> None:
    """If the caller provides no fields to update, the function should bail out
    early without calling SESSION.patch."""
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.update_recurring_investment("s1", account_number="ACC")
    assert out is None
    mock_session.patch.assert_not_called()


def test_update_recurring_investment_auto_resolves_account_number() -> None:
    """If account_number isn't provided, load_account_profile is called."""
    resp = MagicMock(status_code=200, json=lambda: {})
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with (
        patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session),
        patch(
            "robin_stocks.robinhood.recurring_investments.load_account_profile",
            return_value={"account_number": "auto-acct"},
        ) as lap,
    ):
        ri.update_recurring_investment("s1", state="paused")
    lap.assert_called_once()


def test_update_recurring_investment_returns_none_when_no_account_can_be_resolved() -> None:
    """If load_account_profile can't produce an account_number, bail."""
    with patch(
        "robin_stocks.robinhood.recurring_investments.load_account_profile",
        return_value={"foo": "bar"},  # no account_number key
    ):
        out = ri.update_recurring_investment("s1", state="paused")
    assert out is None


def test_update_recurring_investment_jsonify_false_returns_raw_response() -> None:
    """jsonify=False should return the raw Response object (covers update's line 204)."""
    resp = MagicMock(status_code=204)
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.update_recurring_investment("s1", account_number="ACC", state="paused", jsonify=False)
    assert out is resp


def test_update_recurring_investment_error_body_not_parseable_doesnt_crash() -> None:
    """If the error response body isn't JSON, we still log + return None gracefully."""
    resp = MagicMock(status_code=500)
    resp.json.side_effect = ValueError("not JSON")
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.update_recurring_investment("s1", account_number="ACC", state="paused")
    assert out is None


def test_update_recurring_investment_with_all_optional_fields() -> None:
    resp = MagicMock(status_code=200, json=lambda: {})
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        ri.update_recurring_investment(
            "s1",
            account_number="ACC",
            amount=20.0,
            frequency="monthly",
            state="active",
            start_date="2026-12-15",
        )
    body = mock_session.patch.call_args[1]["json"]
    assert body["amount"]["amount"] == "20.0"
    assert body["frequency"] == "monthly"
    assert body["state"] == "active"
    assert body["start_date"] == "2026-12-15"


# ---------------------------------------------------------------------------
# cancel_recurring_investment
# ---------------------------------------------------------------------------


def test_cancel_recurring_investment_uses_patch_with_deleted_state() -> None:
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"state": "deleted"}
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.cancel_recurring_investment("sched-1")

    body = mock_session.patch.call_args[1]["json"]
    assert body == {"state": "deleted"}
    assert out == {"state": "deleted"}


def test_cancel_recurring_investment_returns_none_on_error_status() -> None:
    resp = MagicMock(status_code=403)
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.cancel_recurring_investment("sched-1")
    assert out is None


def test_cancel_recurring_investment_returns_none_on_exception() -> None:
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.side_effect = Exception("network")

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.cancel_recurring_investment("sched-1")
    assert out is None


def test_cancel_recurring_investment_restores_content_type() -> None:
    resp = MagicMock(status_code=200, json=lambda: {})
    mock_session = MagicMock()
    original = "application/x-www-form-urlencoded; charset=utf-8"
    mock_session.headers = {"Content-Type": original}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        ri.cancel_recurring_investment("sched-1")
    assert mock_session.headers["Content-Type"] == original


def test_cancel_recurring_investment_jsonify_false_returns_response() -> None:
    """If jsonify=False, the raw response object is returned instead of .json()."""
    resp = MagicMock(status_code=204)
    mock_session = MagicMock()
    mock_session.headers = {"Content-Type": "x"}
    mock_session.patch.return_value = resp

    with patch("robin_stocks.robinhood.recurring_investments.SESSION", mock_session):
        out = ri.cancel_recurring_investment("sched-1", jsonify=False)
    assert out is resp


# ---------------------------------------------------------------------------
# get_next_investment_date
# ---------------------------------------------------------------------------


def test_get_next_investment_date_defaults_start_date_to_today() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    with patch(
        "robin_stocks.robinhood.recurring_investments.request_get", return_value={"next_investment_date": "2026-05-27"}
    ) as rg:
        out = ri.get_next_investment_date(frequency="weekly")
    url = rg.call_args[0][0]
    assert today in url
    assert "frequency=weekly" in url
    assert out == {"next_investment_date": "2026-05-27"}


def test_get_next_investment_date_explicit_start_date() -> None:
    with patch(
        "robin_stocks.robinhood.recurring_investments.request_get", return_value={"next_investment_date": "2026-06-08"}
    ) as rg:
        ri.get_next_investment_date(frequency="biweekly", start_date="2026-06-01")
    url = rg.call_args[0][0]
    assert "frequency=biweekly" in url
    assert "start_date=2026-06-01" in url
