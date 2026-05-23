"""Tests for the remaining options.py functions not covered by index routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import options


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ---------------------------------------------------------------------------
# find_options_by_expiration_and_strike
# ---------------------------------------------------------------------------


def test_find_options_by_expiration_and_strike_collects() -> None:
    with patch("robin_stocks.robinhood.options.find_tradable_options",
              return_value=[{"expiration_date": "2026-06-19", "id": "o1"}]), \
         patch("robin_stocks.robinhood.options.get_option_market_data_by_id", return_value=[{"delta": "0.5"}]):
        out = options.find_options_by_expiration_and_strike("AAPL", "2026-06-19", "150")
    assert isinstance(out, list)
    assert len(out) == 1


def test_find_options_by_expiration_and_strike_bad_symbol() -> None:
    out = options.find_options_by_expiration_and_strike(123, "2026-06-19", "150", optionType=5)
    assert out == [None]


# ---------------------------------------------------------------------------
# find_options_by_specific_profitability
# ---------------------------------------------------------------------------


def test_find_options_by_specific_profitability_filters_by_range() -> None:
    tradable = [{"expiration_date": "2026-06-19", "id": "o1"}]
    market = [{"chance_of_profit_short": "0.50"}]
    with patch("robin_stocks.robinhood.options.find_tradable_options", return_value=tradable), \
         patch("robin_stocks.robinhood.options.get_option_market_data_by_id", return_value=market):
        out = options.find_options_by_specific_profitability(
            "AAPL", expirationDate="2026-06-19", profitFloor=0.1, profitCeiling=0.9
        )
    assert len(out) == 1


def test_find_options_by_specific_profitability_excludes_out_of_range() -> None:
    tradable = [{"expiration_date": "2026-06-19", "id": "o1"}]
    market = [{"chance_of_profit_short": "0.99"}]
    with patch("robin_stocks.robinhood.options.find_tradable_options", return_value=tradable), \
         patch("robin_stocks.robinhood.options.get_option_market_data_by_id", return_value=market):
        out = options.find_options_by_specific_profitability(
            "AAPL", expirationDate="2026-06-19", profitFloor=0.1, profitCeiling=0.5
        )
    assert out == []


def test_find_options_by_specific_profitability_invalid_typeprofit_defaults() -> None:
    tradable = [{"expiration_date": "2026-06-19", "id": "o1"}]
    market = [{"chance_of_profit_short": "0.5"}]
    with patch("robin_stocks.robinhood.options.find_tradable_options", return_value=tradable), \
         patch("robin_stocks.robinhood.options.get_option_market_data_by_id", return_value=market):
        # Invalid typeProfit triggers the warning + default
        out = options.find_options_by_specific_profitability(
            "AAPL", expirationDate="2026-06-19", typeProfit="bogus"
        )
    assert isinstance(out, list)


# ---------------------------------------------------------------------------
# get_option_market_data / get_option_instrument_data
# ---------------------------------------------------------------------------


def test_get_option_market_data_resolves_id() -> None:
    with patch("robin_stocks.robinhood.options.id_for_option", return_value="opt-1"), \
         patch("robin_stocks.robinhood.options.get_option_market_data_by_id", return_value=[{"delta": "0.5"}]):
        out = options.get_option_market_data("AAPL", "2026-06-19", "150", "call")
    assert isinstance(out, list)


def test_get_option_market_data_bad_symbol() -> None:
    out = options.get_option_market_data(123, "2026-06-19", "150", 5)
    assert out == [None]


def test_get_option_instrument_data_by_id_returns_data() -> None:
    with patch("robin_stocks.robinhood.options.request_get", return_value={"id": "opt-1"}):
        out = options.get_option_instrument_data_by_id("opt-1")
    assert out == {"id": "opt-1"}


def test_get_option_instrument_data_resolves_id() -> None:
    with patch("robin_stocks.robinhood.options.id_for_option", return_value="opt-1"), \
         patch("robin_stocks.robinhood.options.request_get", return_value={"id": "opt-1"}):
        out = options.get_option_instrument_data("AAPL", "2026-06-19", "150", "call")
    assert out == {"id": "opt-1"}


def test_get_option_instrument_data_bad_symbol() -> None:
    out = options.get_option_instrument_data(123, "2026-06-19", "150", 5)
    assert out == [None]


# ---------------------------------------------------------------------------
# get_option_historicals — validation branches
# ---------------------------------------------------------------------------


def test_get_option_historicals_bad_interval() -> None:
    out = options.get_option_historicals("AAPL", "2026-06-19", "150", "call", interval="bogus")
    assert out == [None]


def test_get_option_historicals_bad_span() -> None:
    out = options.get_option_historicals("AAPL", "2026-06-19", "150", "call", span="forever")
    assert out == [None]


def test_get_option_historicals_bad_bounds() -> None:
    out = options.get_option_historicals("AAPL", "2026-06-19", "150", "call", bounds="bogus")
    assert out == [None]


def test_get_option_historicals_bad_symbol() -> None:
    out = options.get_option_historicals(123, "2026-06-19", "150", 5)
    assert out == [None]


def test_get_option_historicals_valid() -> None:
    data = {"data_points": [{"begins_at": "2026-01-01", "close_price": "1.5"}]}
    with patch("robin_stocks.robinhood.options.id_for_option", return_value="opt-1"), \
         patch("robin_stocks.robinhood.options.request_get", return_value=data):
        out = options.get_option_historicals("AAPL", "2026-06-19", "150", "call")
    assert isinstance(out, list)
    assert out[0]["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# _index_chain_symbol already tested; spinner functions are cosmetic
# ---------------------------------------------------------------------------


def test_write_spinner_does_not_raise() -> None:
    """Cosmetic helper; just confirm it runs without error."""
    options.write_spinner()
