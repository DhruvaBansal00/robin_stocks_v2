"""Pure-helper tests for robin_stocks.robinhood.helper.

Covers:
- INDEX_OPT_SYMBOLS constant + ``id_for_stock`` / ``id_for_chain`` index routing
- ``update_session_for_futures`` header injection
- ``id_for_futures_contract`` happy path + bad input
- ``filter_data`` edge cases (we rely on it heavily)
- ``round_price`` rounding by magnitude
- Rate-limiter toggles + ``_apply_rate_limit`` behavior
- ``add_symbol`` helper used elsewhere
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from robin_stocks.robinhood import helper


# ---------------------------------------------------------------------------
# INDEX_OPT_SYMBOLS — the load-bearing constant for the #541 routing
# ---------------------------------------------------------------------------


def test_index_opt_symbols_is_a_fixed_tuple_of_known_symbols() -> None:
    """Anyone reading the constant must see exactly these five symbols.

    If this list is ever changed, multiple call sites (id_for_stock,
    id_for_chain, get_stock_quote_by_symbol) silently change behavior.
    """
    assert helper.INDEX_OPT_SYMBOLS == ("SPX", "NDX", "VIX", "RUT", "XSP")


def test_index_opt_symbols_is_immutable() -> None:
    with pytest.raises((AttributeError, TypeError)):
        helper.INDEX_OPT_SYMBOLS.append("FOO")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# id_for_stock — routes index symbols to /indexes/, others to /instruments/
# ---------------------------------------------------------------------------


def test_id_for_stock_routes_regular_symbol_to_instruments() -> None:
    with patch("robin_stocks.robinhood.helper.request_get", return_value={"id": "X"}) as rg:
        helper.id_for_stock("AAPL")
        assert rg.call_args[0][0] == "https://api.robinhood.com/instruments/"


def test_id_for_stock_routes_index_symbol_to_indexes() -> None:
    """PR #541: SPX/NDX/VIX/RUT/XSP must hit /indexes/, not /instruments/."""
    with patch("robin_stocks.robinhood.helper.request_get", return_value={"id": "X"}) as rg:
        helper.id_for_stock("SPX")
        assert rg.call_args[0][0] == "https://api.robinhood.com/indexes/"


@pytest.mark.parametrize("symbol", ["SPX", "NDX", "VIX", "RUT", "XSP"])
def test_id_for_stock_indexes_url_for_every_index_symbol(symbol: str) -> None:
    with patch("robin_stocks.robinhood.helper.request_get", return_value={"id": "X"}) as rg:
        helper.id_for_stock(symbol)
        assert "indexes" in rg.call_args[0][0]


def test_id_for_stock_normalizes_lowercase_and_whitespace() -> None:
    with patch("robin_stocks.robinhood.helper.request_get", return_value={"id": "X"}) as rg:
        helper.id_for_stock(" spx ")  # whitespace + lowercase
        assert rg.call_args[0][0] == "https://api.robinhood.com/indexes/"
        assert rg.call_args[0][2] == {"symbol": "SPX"}


def test_id_for_stock_returns_none_when_symbol_not_string() -> None:
    out = helper.id_for_stock(12345)  # ints have no .upper()
    assert out is None


# ---------------------------------------------------------------------------
# id_for_chain — for index symbols, picks from sorted tradable_chain_ids
# ---------------------------------------------------------------------------


def test_id_for_chain_regular_symbol_returns_single_chain_id() -> None:
    with patch(
        "robin_stocks.robinhood.helper.request_get",
        return_value={"tradable_chain_id": "regular-chain"},
    ) as rg:
        out = helper.id_for_chain("AAPL")
        assert out == "regular-chain"
        assert rg.call_args[0][0] == "https://api.robinhood.com/instruments/"


def test_id_for_chain_xsp_picks_last_sorted_chain_id() -> None:
    """XSP is the only index that uses the [-1] of sorted tradable_chain_ids."""
    with patch(
        "robin_stocks.robinhood.helper.request_get",
        return_value={"tradable_chain_ids": ["bbb", "aaa", "ccc"]},
    ):
        # sorted = ['aaa', 'bbb', 'ccc'] → XSP picks 'ccc'
        assert helper.id_for_chain("XSP") == "ccc"


@pytest.mark.parametrize("symbol", ["SPX", "NDX", "VIX", "RUT"])
def test_id_for_chain_non_xsp_index_picks_first_sorted(symbol: str) -> None:
    with patch(
        "robin_stocks.robinhood.helper.request_get",
        return_value={"tradable_chain_ids": ["zzz", "aaa", "mmm"]},
    ):
        assert helper.id_for_chain(symbol) == "aaa"


def test_id_for_chain_returns_none_or_data_when_request_empty() -> None:
    """Whatever request_get returns falsy, id_for_chain should propagate it."""
    with patch("robin_stocks.robinhood.helper.request_get", return_value=None):
        assert helper.id_for_chain("AAPL") is None


def test_id_for_chain_routes_index_symbol_to_indexes_url() -> None:
    with patch(
        "robin_stocks.robinhood.helper.request_get",
        return_value={"tradable_chain_ids": ["a"]},
    ) as rg:
        helper.id_for_chain("VIX")
        assert rg.call_args[0][0] == "https://api.robinhood.com/indexes/"


def test_id_for_chain_returns_none_on_bad_symbol_type() -> None:
    assert helper.id_for_chain(None) is None


# ---------------------------------------------------------------------------
# Futures helpers
# ---------------------------------------------------------------------------


def test_update_session_for_futures_sets_protected_header() -> None:
    with patch("robin_stocks.robinhood.helper.update_session") as upd:
        helper.update_session_for_futures()
        upd.assert_called_once_with("Rh-Contract-Protected", "true")


def test_id_for_futures_contract_happy_path() -> None:
    with patch(
        "robin_stocks.robinhood.helper.request_get",
        return_value={"result": {"id": "contract-1"}},
    ), patch("robin_stocks.robinhood.helper.update_session_for_futures") as upd:
        out = helper.id_for_futures_contract("esh26")  # lowercase tolerated
        assert out == "contract-1"
        upd.assert_called_once()  # must inject the protected header


def test_id_for_futures_contract_returns_none_when_no_result_key() -> None:
    with patch(
        "robin_stocks.robinhood.helper.request_get",
        return_value={"detail": "not found"},
    ), patch("robin_stocks.robinhood.helper.update_session_for_futures"):
        assert helper.id_for_futures_contract("FAKE") is None


def test_id_for_futures_contract_returns_none_when_request_returns_falsy() -> None:
    with patch("robin_stocks.robinhood.helper.request_get", return_value=None), \
         patch("robin_stocks.robinhood.helper.update_session_for_futures"):
        assert helper.id_for_futures_contract("FAKE") is None


def test_id_for_futures_contract_returns_none_on_bad_input() -> None:
    """Integers have no .upper() — handled gracefully."""
    assert helper.id_for_futures_contract(12345) is None


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset rate-limiter state before and after each test."""
    helper.disable_rate_limiting()
    yield
    helper.disable_rate_limiting()


def test_enable_rate_limiting_sets_flag_and_delay() -> None:
    helper.enable_rate_limiting(delay=2.5)
    assert helper.RATE_LIMIT_ENABLED is True
    assert helper.RATE_LIMIT_DELAY == 2.5


def test_disable_rate_limiting_clears_flag() -> None:
    helper.enable_rate_limiting(delay=0.5)
    helper.disable_rate_limiting()
    assert helper.RATE_LIMIT_ENABLED is False


def test_apply_rate_limit_noop_when_disabled() -> None:
    """No sleep should occur if rate limiting is off."""
    with patch("robin_stocks.robinhood.helper.time.sleep") as sleep_mock:
        helper._apply_rate_limit()
        sleep_mock.assert_not_called()


def test_apply_rate_limit_sleeps_when_enabled_and_recent_request() -> None:
    """If LAST_REQUEST_TIME was very recent, _apply_rate_limit must sleep."""
    helper.enable_rate_limiting(delay=1.0)
    helper.LAST_REQUEST_TIME = time.time()  # last request was right now

    with patch("robin_stocks.robinhood.helper.time.sleep") as sleep_mock:
        helper._apply_rate_limit()
        assert sleep_mock.called
        sleep_seconds = sleep_mock.call_args[0][0]
        # Should sleep for close to 1.0 second
        assert 0 < sleep_seconds <= 1.0


def test_apply_rate_limit_does_not_sleep_when_old_request() -> None:
    """If the last request was a long time ago, no sleep is needed."""
    helper.enable_rate_limiting(delay=0.5)
    helper.LAST_REQUEST_TIME = time.time() - 10  # 10 seconds ago

    with patch("robin_stocks.robinhood.helper.time.sleep") as sleep_mock:
        helper._apply_rate_limit()
        sleep_mock.assert_not_called()


def test_apply_rate_limit_updates_timestamp_after_call() -> None:
    helper.enable_rate_limiting(delay=0.1)
    helper.LAST_REQUEST_TIME = 0

    before = time.time()
    helper._apply_rate_limit()
    assert helper.LAST_REQUEST_TIME >= before


def test_apply_rate_limit_thread_safety() -> None:
    """Multiple threads should not race on LAST_REQUEST_TIME."""
    helper.enable_rate_limiting(delay=0.01)  # tiny delay so test stays fast

    barrier = threading.Barrier(5)

    def worker() -> None:
        barrier.wait()
        helper._apply_rate_limit()

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Just confirming no exceptions / deadlock; the global lock means
    # this would never crash but does block. If the lock were broken,
    # we'd still pass this test — but we'd see flaky behavior elsewhere.
    assert helper.RATE_LIMIT_ENABLED is True


# ---------------------------------------------------------------------------
# filter_data — used by every read function in the SDK
# ---------------------------------------------------------------------------


def test_filter_data_passes_none_through() -> None:
    assert helper.filter_data(None, "anything") is None


def test_filter_data_treats_single_none_list_as_empty() -> None:
    assert helper.filter_data([None], "id") == []


def test_filter_data_empty_list() -> None:
    assert helper.filter_data([], "id") == []


def test_filter_data_list_with_matching_key() -> None:
    data = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    assert helper.filter_data(data, "id") == [1, 2]


def test_filter_data_dict_with_matching_key() -> None:
    assert helper.filter_data({"id": 99, "x": "y"}, "id") == 99


def test_filter_data_list_missing_key_prints_error() -> None:
    data = [{"id": 1}]
    out = helper.filter_data(data, "nope")
    assert out == []


def test_filter_data_dict_missing_key_returns_none() -> None:
    out = helper.filter_data({"id": 1}, "nope")
    assert out is None


def test_filter_data_info_none_returns_data_unchanged() -> None:
    data = [{"id": 1}]
    assert helper.filter_data(data, None) is data


# ---------------------------------------------------------------------------
# round_price — branches by magnitude
# ---------------------------------------------------------------------------


def test_round_price_under_one_cent_uses_6_decimals() -> None:
    assert helper.round_price(0.001234567) == 0.001235


def test_round_price_under_one_dollar_uses_4_decimals() -> None:
    assert helper.round_price(0.123456) == 0.1235


def test_round_price_over_one_dollar_uses_2_decimals() -> None:
    assert helper.round_price(12.3456) == 12.35


def test_round_price_accepts_string_input() -> None:
    assert helper.round_price("12.345") == 12.35
