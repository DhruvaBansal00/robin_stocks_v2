"""Stock-quote routing tests (PR #541).

``get_stock_quote_by_symbol`` must route index symbols (SPX, NDX, etc.)
through ``get_index_quote_by_id`` + the new marketdata-indexes endpoint,
not the regular marketdata-quotes endpoint.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import stocks


def test_get_stock_quote_by_symbol_regular_uses_stock_quote_path() -> None:
    with (
        patch("robin_stocks.robinhood.stocks.id_for_stock", return_value="inst-1"),
        patch("robin_stocks.robinhood.stocks.get_stock_quote_by_id", return_value={"last": "100"}) as sq,
        patch("robin_stocks.robinhood.stocks.get_index_quote_by_id") as iq,
    ):
        out = stocks.get_stock_quote_by_symbol("AAPL")
    sq.assert_called_once_with("inst-1")
    iq.assert_not_called()
    assert out == {"last": "100"}


@pytest.mark.parametrize("symbol", ["SPX", "NDX", "VIX", "RUT", "XSP"])
def test_get_stock_quote_by_symbol_index_uses_index_quote_path(symbol: str) -> None:
    with (
        patch("robin_stocks.robinhood.stocks.id_for_stock", return_value="idx-1"),
        patch("robin_stocks.robinhood.stocks.get_stock_quote_by_id") as sq,
        patch("robin_stocks.robinhood.stocks.get_index_quote_by_id", return_value={"last": "5000"}) as iq,
    ):
        out = stocks.get_stock_quote_by_symbol(symbol)
    iq.assert_called_once_with("idx-1")
    sq.assert_not_called()
    assert out == {"last": "5000"}


def test_get_index_quote_by_id_uses_indexes_url() -> None:
    """The new helper must hit the indexes-values endpoint, not /marketdata/quotes/."""
    with patch("robin_stocks.robinhood.stocks.request_get", return_value={"last": "5000"}) as rg:
        out = stocks.get_index_quote_by_id("idx-1")
    assert rg.call_args[0][0] == "https://api.robinhood.com/marketdata/indexes/values/v1/idx-1/"
    assert out == {"last": "5000"}


def test_get_index_quote_by_id_filters_by_info() -> None:
    """Result should be passed through filter_data."""
    payload = {"last_trade_price": "5000", "instrument": "i"}
    with patch("robin_stocks.robinhood.stocks.request_get", return_value=payload):
        out = stocks.get_index_quote_by_id("idx-1", info="last_trade_price")
    assert out == "5000"
