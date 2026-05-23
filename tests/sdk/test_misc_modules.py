"""Sweep tests for options (non-routing), markets, profiles, crypto, and export.

Mock-based dispatch checks to confirm each public function reaches its endpoint
without error and applies the expected filter mode.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import crypto, export, markets, options, profiles


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ===========================================================================
# options.py
# ===========================================================================


@pytest.fixture
def opt_rg():
    with patch("robin_stocks.robinhood.options.request_get") as m:
        m.return_value = []
        yield m


def test_get_aggregate_positions_uses_pagination(opt_rg) -> None:
    opt_rg.return_value = [{"id": "1"}]
    options.get_aggregate_positions()
    assert opt_rg.call_args[0][1] == "pagination"


def test_get_aggregate_open_positions_uses_pagination(opt_rg) -> None:
    opt_rg.return_value = [{"id": "1"}]
    options.get_aggregate_open_positions()
    assert opt_rg.call_args[0][1] == "pagination"


def test_get_market_options_uses_pagination(opt_rg) -> None:
    opt_rg.return_value = [{"id": "1"}]
    options.get_market_options()
    assert opt_rg.call_args[0][1] == "pagination"


def test_get_all_option_positions_uses_pagination(opt_rg) -> None:
    opt_rg.return_value = [{"id": "1"}]
    options.get_all_option_positions()
    assert opt_rg.call_args[0][1] == "pagination"


def test_get_open_option_positions_uses_nonzero(opt_rg) -> None:
    opt_rg.return_value = [{"id": "1"}]
    options.get_open_option_positions()
    # payload includes a nonzero filter (the impl uses 'True')
    assert any(isinstance(a, dict) and "nonzero" in a for a in opt_rg.call_args[0])


def test_get_chains_returns_data(opt_rg) -> None:
    opt_rg.return_value = {"expiration_dates": []}
    with patch("robin_stocks.robinhood.options.id_for_stock", return_value="inst-1"):
        out = options.get_chains("AAPL")
    assert out is not None


def test_get_option_market_data_by_id_returns_data(opt_rg) -> None:
    opt_rg.return_value = [{"delta": "0.5"}]
    with patch(
        "robin_stocks.robinhood.options.get_option_instrument_data_by_id",
        return_value={"url": "https://api/options/instruments/opt-1/"},
    ):
        out = options.get_option_market_data_by_id("opt-1")
    assert out is not None


def test_get_option_market_data_by_id_returns_none_when_instrument_missing(opt_rg) -> None:
    with patch("robin_stocks.robinhood.options.get_option_instrument_data_by_id", return_value=None):
        out = options.get_option_market_data_by_id("opt-1")
    assert out is None


def test_get_option_instrument_data_by_id_returns_data(opt_rg) -> None:
    opt_rg.return_value = {"id": "opt-1"}
    out = options.get_option_instrument_data_by_id("opt-1")
    assert out == {"id": "opt-1"}


def test_find_options_by_expiration_collects(opt_rg) -> None:
    with (
        patch(
            "robin_stocks.robinhood.options.find_tradable_options",
            return_value=[{"expiration_date": "2026-06-19", "strike_price": "100", "id": "o1"}],
        ),
        patch("robin_stocks.robinhood.options.get_option_market_data_by_id", return_value=[{"delta": "0.5"}]),
    ):
        out = options.find_options_by_expiration("AAPL", "2026-06-19")
    assert isinstance(out, list)
    assert len(out) == 1


def test_find_options_by_strike_collects(opt_rg) -> None:
    with (
        patch("robin_stocks.robinhood.options.find_tradable_options", return_value=[{"strike_price": "100.0000", "id": "o1"}]),
        patch("robin_stocks.robinhood.options.get_option_market_data_by_id", return_value=[{}]),
    ):
        out = options.find_options_by_strike("AAPL", 100)
    assert isinstance(out, list)


# ===========================================================================
# markets.py
# ===========================================================================


@pytest.fixture
def mkt_rg():
    with patch("robin_stocks.robinhood.markets.request_get") as m:
        m.return_value = []
        yield m


def test_get_top_100_returns_results(mkt_rg) -> None:
    mkt_rg.return_value = {"instruments": []}
    with patch("robin_stocks.robinhood.markets.get_all_stocks_from_market_tag", return_value=[]):
        markets.get_top_100()


def test_get_top_movers_returns_results(mkt_rg) -> None:
    mkt_rg.return_value = {"instruments": []}
    with patch("robin_stocks.robinhood.markets.get_all_stocks_from_market_tag", return_value=[]):
        markets.get_top_movers()


def test_get_top_movers_sp500_up(mkt_rg) -> None:
    mkt_rg.return_value = [{"symbol": "AAPL"}]
    markets.get_top_movers_sp500("up")
    mkt_rg.assert_called()


def test_get_top_movers_sp500_rejects_bad_direction(mkt_rg) -> None:
    out = markets.get_top_movers_sp500("sideways")
    assert out == [None]


def test_get_markets_uses_pagination(mkt_rg) -> None:
    mkt_rg.return_value = [{"name": "NASDAQ"}]
    markets.get_markets()
    assert mkt_rg.call_args[0][1] == "pagination"


def test_get_currency_pairs_returns_results(mkt_rg) -> None:
    mkt_rg.return_value = [{"id": "1"}]
    markets.get_currency_pairs()
    mkt_rg.assert_called()


def test_get_market_hours_returns_data(mkt_rg) -> None:
    mkt_rg.return_value = {"opens_at": "9:30"}
    out = markets.get_market_hours("XNYS", "2026-05-22")
    assert out == {"opens_at": "9:30"}


def test_get_market_today_hours_returns_data(mkt_rg) -> None:
    mkt_rg.return_value = {"opens_at": "9:30"}
    with patch("robin_stocks.robinhood.markets.get_markets", return_value=[{"mic": "XNYS", "todays_hours": "url"}]):
        markets.get_market_today_hours("XNYS")


# ===========================================================================
# profiles.py
# ===========================================================================


@pytest.fixture
def prof_rg():
    with patch("robin_stocks.robinhood.profiles.request_get") as m:
        m.return_value = {}
        yield m


def test_load_account_profile_indexzero(prof_rg) -> None:
    prof_rg.return_value = {"account_number": "ACC"}
    out = profiles.load_account_profile()
    assert out == {"account_number": "ACC"}


def test_load_basic_profile_returns_data(prof_rg) -> None:
    prof_rg.return_value = {"city": "SF"}
    assert profiles.load_basic_profile() == {"city": "SF"}


def test_load_investment_profile_returns_data(prof_rg) -> None:
    prof_rg.return_value = {"risk_tolerance": "high"}
    assert profiles.load_investment_profile() == {"risk_tolerance": "high"}


def test_load_portfolio_profile_returns_data(prof_rg) -> None:
    prof_rg.return_value = {"equity": "100"}
    assert profiles.load_portfolio_profile() == {"equity": "100"}


def test_load_security_profile_returns_data(prof_rg) -> None:
    prof_rg.return_value = {"object": "x"}
    assert profiles.load_security_profile() == {"object": "x"}


def test_load_user_profile_returns_data(prof_rg) -> None:
    prof_rg.return_value = {"username": "u"}
    assert profiles.load_user_profile() == {"username": "u"}


# ===========================================================================
# crypto.py (beyond get_open_crypto_positions, which has its own file)
# ===========================================================================


@pytest.fixture
def crypto_rg():
    with patch("robin_stocks.robinhood.crypto.request_get") as m:
        m.return_value = []
        yield m


def test_load_crypto_profile_returns_data(crypto_rg) -> None:
    crypto_rg.return_value = {"id": "crypto-acct"}
    assert crypto.load_crypto_profile() == {"id": "crypto-acct"}


def test_get_crypto_positions_uses_pagination(crypto_rg) -> None:
    crypto_rg.return_value = [{"id": "1"}]
    crypto.get_crypto_positions()
    assert crypto_rg.call_args[0][1] == "pagination"


def test_get_crypto_currency_pairs_returns_results(crypto_rg) -> None:
    crypto_rg.return_value = [{"id": "1"}]
    crypto.get_crypto_currency_pairs()
    crypto_rg.assert_called()


def test_get_crypto_info_returns_data(crypto_rg) -> None:
    # get_crypto_info filters the currency-pairs list by asset_currency code
    crypto_rg.return_value = [
        {"id": "btc", "asset_currency": {"code": "BTC"}},
        {"id": "eth", "asset_currency": {"code": "ETH"}},
    ]
    out = crypto.get_crypto_info("BTC")
    assert out["id"] == "btc"


def test_get_crypto_info_returns_none_when_symbol_missing(crypto_rg) -> None:
    crypto_rg.return_value = [{"id": "btc", "asset_currency": {"code": "BTC"}}]
    out = crypto.get_crypto_info("DOGE")
    assert out is None


def test_get_crypto_quote_resolves_id_then_fetches(crypto_rg) -> None:
    crypto_rg.return_value = {"mark_price": "50000"}
    with patch("robin_stocks.robinhood.crypto.get_crypto_info", return_value={"id": "btc-id"}):
        out = crypto.get_crypto_quote("BTC")
    assert out is not None


def test_get_crypto_quote_from_id_returns_data(crypto_rg) -> None:
    crypto_rg.return_value = {"mark_price": "50000"}
    out = crypto.get_crypto_quote_from_id("btc-id")
    assert out == {"mark_price": "50000"}


def test_get_crypto_historicals_valid_args(crypto_rg) -> None:
    crypto_rg.return_value = {"symbol": "BTCUSD", "data_points": [{"close_price": "50000"}]}
    with patch("robin_stocks.robinhood.crypto.get_crypto_info", return_value="btc-id"):
        out = crypto.get_crypto_historicals("BTC")
    crypto_rg.assert_called()
    assert out[0]["symbol"] == "BTCUSD"


def test_get_crypto_historicals_rejects_bad_interval(crypto_rg) -> None:
    with patch("robin_stocks.robinhood.crypto.get_crypto_info", return_value={"id": "btc-id"}):
        out = crypto.get_crypto_historicals("BTC", interval="bogus")
    assert out == [None]


# ===========================================================================
# export.py
# ===========================================================================


def test_fix_file_extension_adds_csv() -> None:
    # Returns a resolved Path object
    assert str(export.fix_file_extension("orders")).endswith(".csv")


def test_fix_file_extension_keeps_existing_csv() -> None:
    out = str(export.fix_file_extension("orders.csv"))
    assert out.endswith(".csv")
    assert out.count(".csv") == 1


def test_create_absolute_csv_with_name() -> None:
    out = str(export.create_absolute_csv("/tmp", "orders", "stock"))
    assert out.endswith(".csv")


def test_create_absolute_csv_defaults_name_from_order_type() -> None:
    """When file_name is empty, the name is derived from the order_type + date."""
    out = str(export.create_absolute_csv("/tmp", "", "option"))
    assert "option_orders_" in out
    assert out.endswith(".csv")


def test_export_completed_stock_orders_writes_csv(tmp_path) -> None:
    """Exercises the stock-order CSV export against mocked order + instrument data."""
    orders_data = [
        {
            "state": "filled",
            "side": "buy",
            "instrument": "https://api/i/1/",
            "average_price": "100.00",
            "quantity": "1",
            "cancel": None,
            "fees": "0.00",
            "last_transaction_at": "2026-01-01T00:00:00Z",
            "type": "market",
            "executions": [],
        }
    ]
    with (
        patch("robin_stocks.robinhood.export.get_all_stock_orders", return_value=orders_data),
        patch("robin_stocks.robinhood.export.get_symbol_by_url", return_value="AAPL"),
    ):
        # file_name=None → relative default name, lands inside dir_path
        export.export_completed_stock_orders(str(tmp_path), file_name=None)
    written = list(tmp_path.glob("*.csv"))
    assert len(written) == 1


def test_export_completed_crypto_orders_writes_csv(tmp_path) -> None:
    orders_data = [
        {
            "state": "filled",
            "side": "buy",
            "cancel_url": None,
            "currency_pair_id": "pair-1",
            "average_price": "50000",
            "quantity": "0.1",
            "fees": "0.00",
            "last_transaction_at": "2026-01-01T00:00:00Z",
            "type": "market",
        }
    ]
    with (
        patch("robin_stocks.robinhood.export.get_all_crypto_orders", return_value=orders_data),
        patch("robin_stocks.robinhood.export.get_crypto_quote_from_id", return_value="BTC"),
    ):
        export.export_completed_crypto_orders(str(tmp_path), file_name=None)
    written = list(tmp_path.glob("*.csv"))
    assert len(written) == 1
