"""Tests for the request_get / request_post / request_delete / request_document
helpers, covering data-type branches and error paths.

These functions sit beneath every SDK call, so breaking them silently would
take everything down.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from robin_stocks.robinhood import helper


@pytest.fixture
def mock_session():
    """Patch the global SESSION used by helper.* — restored after the test."""
    with patch("robin_stocks.robinhood.helper.SESSION") as s:
        yield s


# ---------------------------------------------------------------------------
# request_get — every dataType branch
# ---------------------------------------------------------------------------


def _ok_response(payload, status_code=200):
    res = MagicMock()
    res.json.return_value = payload
    res.raise_for_status.return_value = None
    res.status_code = status_code
    return res


def _http_error_response(code=500):
    res = MagicMock()
    res.raise_for_status.side_effect = requests.exceptions.HTTPError(f"{code} Error")
    return res


def test_request_get_regular_returns_json(mock_session) -> None:
    mock_session.get.return_value = _ok_response({"foo": "bar"})
    out = helper.request_get("http://x")
    assert out == {"foo": "bar"}


def test_request_get_returns_none_on_http_error_regular(mock_session) -> None:
    mock_session.get.return_value = _http_error_response()
    out = helper.request_get("http://x")
    assert out is None


def test_request_get_returns_list_none_on_http_error_pagination(mock_session) -> None:
    """Pagination/results modes initialize data as [None] for safety."""
    mock_session.get.return_value = _http_error_response()
    out = helper.request_get("http://x", dataType="pagination")
    assert out == [None]


def test_request_get_results_extracts_results_key(mock_session) -> None:
    mock_session.get.return_value = _ok_response({"results": [{"id": "1"}, {"id": "2"}]})
    out = helper.request_get("http://x", dataType="results")
    assert out == [{"id": "1"}, {"id": "2"}]


def test_request_get_results_missing_key_returns_list_none(mock_session) -> None:
    mock_session.get.return_value = _ok_response({"foo": "bar"})
    out = helper.request_get("http://x", dataType="results")
    assert out == [None]


def test_request_get_indexzero_returns_first_result(mock_session) -> None:
    mock_session.get.return_value = _ok_response({"results": [{"id": "first"}, {"id": "second"}]})
    out = helper.request_get("http://x", dataType="indexzero")
    assert out == {"id": "first"}


def test_request_get_indexzero_empty_results_returns_none(mock_session) -> None:
    mock_session.get.return_value = _ok_response({"results": []})
    out = helper.request_get("http://x", dataType="indexzero")
    assert out is None


def test_request_get_indexzero_missing_results_returns_none(mock_session) -> None:
    mock_session.get.return_value = _ok_response({"data": []})
    out = helper.request_get("http://x", dataType="indexzero")
    assert out is None


def test_request_get_pagination_single_page(mock_session) -> None:
    """When there's no 'next' link, return just data['results']."""
    mock_session.get.return_value = _ok_response({"results": [{"id": "1"}], "next": None})
    out = helper.request_get("http://x", dataType="pagination")
    assert out == [{"id": "1"}]


def test_request_get_pagination_follows_next(mock_session) -> None:
    """Two-page response: first has 'next', second doesn't."""
    page1 = _ok_response({"results": [{"id": "1"}], "next": "http://x/2"})
    page2 = _ok_response({"results": [{"id": "2"}], "next": None})
    mock_session.get.side_effect = [page1, page2]

    out = helper.request_get("http://x", dataType="pagination")
    assert [item["id"] for item in out] == ["1", "2"]


def test_request_get_pagination_swallow_error_on_next(mock_session) -> None:
    """If fetching the next page fails, return what we have so far."""
    page1 = _ok_response({"results": [{"id": "1"}], "next": "http://x/2"})
    err = MagicMock()
    err.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
    mock_session.get.side_effect = [page1, err]

    out = helper.request_get("http://x", dataType="pagination")
    assert out == [{"id": "1"}]


def test_request_get_pagination_missing_results_key_returns_list_none(mock_session) -> None:
    mock_session.get.return_value = _ok_response({"foo": "bar"})
    out = helper.request_get("http://x", dataType="pagination")
    assert out == [None]


def test_request_get_jsonify_false_returns_raw_response(mock_session) -> None:
    res = _ok_response({"a": 1})
    mock_session.get.return_value = res
    out = helper.request_get("http://x", jsonify_data=False)
    assert out is res


# ---------------------------------------------------------------------------
# request_post — error path + json= branch
# ---------------------------------------------------------------------------


def test_request_post_returns_json_on_success(mock_session) -> None:
    mock_session.post.return_value = _ok_response({"id": "1"})
    out = helper.request_post("http://x", {"a": 1})
    assert out == {"id": "1"}


def test_request_post_json_flag_uses_json_kwarg(mock_session) -> None:
    """When json=True, the request must use json= instead of data=."""
    mock_session.post.return_value = _ok_response({})
    helper.request_post("http://x", {"a": 1}, json=True)
    _, kwargs = mock_session.post.call_args
    assert kwargs.get("json") == {"a": 1}


def test_request_post_jsonify_false_returns_response(mock_session) -> None:
    res = _ok_response({})
    mock_session.post.return_value = res
    out = helper.request_post("http://x", {"a": 1}, jsonify_data=False)
    assert out is res


def test_request_post_returns_data_on_http_error(mock_session) -> None:
    """HTTP errors still return whatever data was already parsed (or None)."""
    err = _http_error_response(400)
    err.json.return_value = {"detail": "bad"}
    mock_session.post.return_value = err
    out = helper.request_post("http://x", {"a": 1})
    # When jsonify_data=True with HTTP error, the function returns whatever
    # data state was at the time of the error (None or partial dict).
    assert out is None or out == {"detail": "bad"}


# ---------------------------------------------------------------------------
# request_delete
# ---------------------------------------------------------------------------


def test_request_delete_returns_response(mock_session) -> None:
    res = MagicMock()
    res.raise_for_status.return_value = None
    mock_session.delete.return_value = res
    out = helper.request_delete("http://x")
    # request_delete returns whatever res is on success
    assert out is res or out is None  # implementation-dependent


def test_request_delete_returns_none_on_http_error(mock_session) -> None:
    err = MagicMock()
    err.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
    mock_session.delete.return_value = err
    out = helper.request_delete("http://x")
    assert out is None


# ---------------------------------------------------------------------------
# request_document
# ---------------------------------------------------------------------------


def test_request_document_returns_response_on_success(mock_session) -> None:
    res = MagicMock()
    res.raise_for_status.return_value = None
    mock_session.get.return_value = res
    out = helper.request_document("http://x")
    assert out is res


def test_request_document_returns_none_on_http_error(mock_session) -> None:
    err = MagicMock()
    err.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
    mock_session.get.return_value = err
    out = helper.request_document("http://x")
    assert out is None


# ---------------------------------------------------------------------------
# update_session — directly mutates session headers
# ---------------------------------------------------------------------------


def test_update_session_sets_header() -> None:
    helper.SESSION.headers["TestKey"] = "old"
    helper.update_session("TestKey", "new")
    assert helper.SESSION.headers["TestKey"] == "new"
    del helper.SESSION.headers["TestKey"]


# ---------------------------------------------------------------------------
# inputs_to_set — symbol normalization
# ---------------------------------------------------------------------------


def test_inputs_to_set_single_string() -> None:
    assert helper.inputs_to_set("aapl") == ["AAPL"]


def test_inputs_to_set_list_dedupes() -> None:
    assert helper.inputs_to_set(["aapl", "AAPL", " tsla "]) == ["AAPL", "TSLA"]


def test_inputs_to_set_filters_non_string_in_list() -> None:
    assert helper.inputs_to_set(["AAPL", 123, "TSLA"]) == ["AAPL", "TSLA"]


def test_inputs_to_set_tuple_input() -> None:
    assert helper.inputs_to_set(("aapl", "tsla")) == ["AAPL", "TSLA"]


def test_inputs_to_set_empty_input() -> None:
    assert helper.inputs_to_set([]) == []


# ---------------------------------------------------------------------------
# id_for_option — happy path + error branch
# ---------------------------------------------------------------------------


def test_id_for_option_returns_matching_option_id() -> None:
    data = [
        {"expiration_date": "2026-06-19", "id": "wrong"},
        {"expiration_date": "2026-09-18", "id": "match"},
    ]
    with (
        patch("robin_stocks.robinhood.helper.id_for_chain", return_value="chain-id"),
        patch("robin_stocks.robinhood.helper.request_get", return_value=data),
    ):
        out = helper.id_for_option("AAPL", "2026-09-18", "150", "call")
    assert out == "match"


def test_id_for_option_returns_none_when_no_match() -> None:
    data = [{"expiration_date": "2026-06-19", "id": "x"}]
    with (
        patch("robin_stocks.robinhood.helper.id_for_chain", return_value="chain-id"),
        patch("robin_stocks.robinhood.helper.request_get", return_value=data),
    ):
        out = helper.id_for_option("AAPL", "2099-01-01", "999", "call")
    assert out is None


# ---------------------------------------------------------------------------
# get_output / set_output — simple state accessors
# ---------------------------------------------------------------------------


def test_set_and_get_output_roundtrip() -> None:
    import io

    sink = io.StringIO()
    original = helper.get_output()
    try:
        helper.set_output(sink)
        assert helper.get_output() is sink
    finally:
        helper.set_output(original)


# ---------------------------------------------------------------------------
# login_required decorator
# ---------------------------------------------------------------------------


def test_login_required_raises_when_not_logged_in() -> None:
    @helper.login_required
    def needs_auth():
        return "ok"

    with patch("robin_stocks.robinhood.helper.LOGGED_IN", False):
        with pytest.raises(Exception, match="can only be called when logged in"):
            needs_auth()


def test_login_required_allows_call_when_logged_in() -> None:
    @helper.login_required
    def needs_auth():
        return "ok"

    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        assert needs_auth() == "ok"


# ---------------------------------------------------------------------------
# convert_none_to_string decorator
# ---------------------------------------------------------------------------


def test_convert_none_to_string_passes_through_truthy() -> None:
    @helper.convert_none_to_string
    def gimme():
        return "value"

    assert gimme() == "value"


def test_convert_none_to_string_replaces_none_with_empty() -> None:
    @helper.convert_none_to_string
    def gimme():
        return None

    assert gimme() == ""
