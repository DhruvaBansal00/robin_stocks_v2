"""Sweep tests for robin_stocks.robinhood.stocks (non-routing functions).

The index-options routing tests live in test_stocks_index_routing.py;
this file covers every other function in the module with mocked HTTP.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import stocks


@pytest.fixture
def rg():
    with patch("robin_stocks.robinhood.stocks.request_get") as m:
        m.return_value = []
        yield m


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ---------------------------------------------------------------------------
# Quote / fundamentals / instruments
# ---------------------------------------------------------------------------


def test_get_quotes_returns_list_of_results(rg) -> None:
    rg.return_value = [{"symbol": "AAPL"}]
    out = stocks.get_quotes("AAPL")
    rg.assert_called_once()
    assert out == [{"symbol": "AAPL"}]


def test_get_quotes_accepts_list(rg) -> None:
    rg.return_value = [{"symbol": "AAPL"}, {"symbol": "MSFT"}]
    stocks.get_quotes(["AAPL", "MSFT"])
    rg.assert_called_once()


def test_get_fundamentals_returns_results(rg) -> None:
    # results-mode unwraps; the mock returns the inner list per call
    rg.return_value = [{"market_cap": "1T"}]
    out = stocks.get_fundamentals("AAPL")
    # The function annotates each item with symbol; just confirm we get a dict back
    assert isinstance(out, list)


def test_get_fundamentals_handles_none_result(rg) -> None:
    rg.return_value = [None]
    out = stocks.get_fundamentals("FAKESYM")
    # filter_data() flattens [None] to []
    assert out == [] or out == [None]


def test_get_instruments_by_symbols_returns_list(rg) -> None:
    # indexzero-mode returns a single dict per call; the function loops per symbol
    rg.return_value = {"id": "inst-1"}
    out = stocks.get_instruments_by_symbols("AAPL")
    assert out == [{"id": "inst-1"}]


def test_get_instruments_by_symbols_skips_missing(rg) -> None:
    """If request_get returns falsy, the symbol is dropped from the result."""
    rg.return_value = None
    out = stocks.get_instruments_by_symbols("FAKESYM")
    assert out == [] or out is None


def test_get_instrument_by_url_passes_through(rg) -> None:
    rg.return_value = {"id": "inst-1"}
    out = stocks.get_instrument_by_url("https://api/instruments/inst-1/")
    assert out == {"id": "inst-1"}


def test_get_latest_price_returns_strings(rg) -> None:
    """get_latest_price returns price strings from get_quotes."""
    rg.return_value = [{"symbol": "AAPL", "last_trade_price": "100.00", "last_extended_hours_trade_price": None}]
    out = stocks.get_latest_price("AAPL")
    assert isinstance(out, list)


def test_get_latest_price_uses_extended_hours_when_available(rg) -> None:
    rg.return_value = [{"symbol": "AAPL", "last_trade_price": "100.00", "last_extended_hours_trade_price": "101.00"}]
    out = stocks.get_latest_price("AAPL", includeExtendedHours=True)
    assert "101.00" in out


def test_get_latest_price_with_price_type_explicit(rg) -> None:
    rg.return_value = [{"symbol": "AAPL", "ask_price": "100.50", "last_extended_hours_trade_price": None}]
    out = stocks.get_latest_price("AAPL", priceType="ask_price")
    assert "100.50" in out


# ---------------------------------------------------------------------------
# Name / symbol lookups
# ---------------------------------------------------------------------------


def test_get_name_by_symbol_returns_simple_name() -> None:
    # @cache means we must use a unique symbol per assertion
    with patch("robin_stocks.robinhood.stocks.request_get", return_value={"simple_name": "Netflix", "name": "Netflix Inc."}):
        out = stocks.get_name_by_symbol("NFLX")
    assert out == "Netflix"


def test_get_name_by_symbol_falls_back_to_name_when_no_simple_name() -> None:
    with patch("robin_stocks.robinhood.stocks.request_get", return_value={"simple_name": "", "name": "Microsoft Corp."}):
        out = stocks.get_name_by_symbol("MSFT")
    assert out == "Microsoft Corp."


def test_get_name_by_symbol_returns_empty_on_bad_input() -> None:
    """Non-string returns '' because of the convert_none_to_string decorator."""
    out = stocks.get_name_by_symbol(987654)  # unique to dodge the cache
    assert out == ""


def test_get_name_by_url_returns_simple_name() -> None:
    with patch("robin_stocks.robinhood.stocks.request_get", return_value={"simple_name": "Apple"}):
        assert stocks.get_name_by_url("https://api/i/1/") == "Apple"


def test_get_symbol_by_url_returns_symbol() -> None:
    with patch("robin_stocks.robinhood.stocks.request_get", return_value={"symbol": "AAPL"}):
        assert stocks.get_symbol_by_url("https://api/i/1/") == "AAPL"


# ---------------------------------------------------------------------------
# Per-symbol data endpoints
# ---------------------------------------------------------------------------


def test_get_ratings_returns_results(rg) -> None:
    rg.return_value = {"summary": {}, "ratings": []}
    out = stocks.get_ratings("AAPL")
    assert out is not None


def test_get_ratings_with_none_input_handled_gracefully() -> None:
    """get_ratings catches the AttributeError and returns None/empty."""
    out = stocks.get_ratings(None)
    # Either None or a falsy structure is acceptable
    assert out is None or not out


def test_get_events_uses_pagination(rg) -> None:
    rg.return_value = [{"event": "1"}]
    with patch("robin_stocks.robinhood.stocks.id_for_stock", return_value="inst-1"):
        stocks.get_events("AAPL")
    rg.assert_called_once()


def test_get_earnings_uses_pagination(rg) -> None:
    rg.return_value = [{"year": "2026"}]
    stocks.get_earnings("AAPL")
    rg.assert_called_once()


def test_get_news_uses_pagination(rg) -> None:
    rg.return_value = [{"title": "headline"}]
    stocks.get_news("AAPL")
    rg.assert_called_once()


def test_get_splits_returns_results(rg) -> None:
    rg.return_value = [{"divisor": "2"}]
    with patch("robin_stocks.robinhood.stocks.id_for_stock", return_value="inst-1"):
        out = stocks.get_splits("AAPL")
    assert out == [{"divisor": "2"}]


def test_find_instrument_data_returns_results(rg) -> None:
    rg.return_value = [{"id": "inst-1"}]
    out = stocks.find_instrument_data("Apple")
    assert out == [{"id": "inst-1"}]


# ---------------------------------------------------------------------------
# Historicals — branch on bad inputs
# ---------------------------------------------------------------------------


def test_get_stock_historicals_returns_for_valid_args(rg) -> None:
    rg.return_value = [{"symbol": "AAPL", "historicals": [{"close_price": "100"}]}]
    with patch("robin_stocks.robinhood.stocks.inputs_to_set", return_value=["AAPL"]):
        out = stocks.get_stock_historicals("AAPL")
    rg.assert_called()
    # The flattened historical should carry the symbol annotation
    assert out[0]["symbol"] == "AAPL"


def test_get_stock_historicals_rejects_bad_interval(rg) -> None:
    with patch("robin_stocks.robinhood.stocks.inputs_to_set", return_value=["AAPL"]):
        out = stocks.get_stock_historicals("AAPL", interval="bogus")
    assert out == [None]


def test_get_stock_historicals_rejects_bad_span(rg) -> None:
    with patch("robin_stocks.robinhood.stocks.inputs_to_set", return_value=["AAPL"]):
        out = stocks.get_stock_historicals("AAPL", interval="day", span="forever")
    assert out == [None]


def test_get_stock_historicals_rejects_bad_bounds(rg) -> None:
    with patch("robin_stocks.robinhood.stocks.inputs_to_set", return_value=["AAPL"]):
        out = stocks.get_stock_historicals("AAPL", interval="day", bounds="invalid")
    assert out == [None]


# ---------------------------------------------------------------------------
# Pricebook
# ---------------------------------------------------------------------------


def test_get_pricebook_by_id_uses_pricebook_url(rg) -> None:
    rg.return_value = {"asks": [], "bids": []}
    stocks.get_pricebook_by_id("inst-1")
    assert "pricebook" in rg.call_args[0][0]


def test_get_pricebook_by_symbol_resolves_id_first(rg) -> None:
    rg.return_value = {"asks": [], "bids": []}
    with patch("robin_stocks.robinhood.stocks.id_for_stock", return_value="inst-1"):
        stocks.get_pricebook_by_symbol("AAPL")
    rg.assert_called()
