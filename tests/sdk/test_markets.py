"""Sweep tests for robin_stocks.robinhood.markets — fills remaining branches."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import markets


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


def test_get_top_movers_sp500_bad_direction_type_returns_none() -> None:
    """A non-string direction trips the AttributeError branch."""
    assert markets.get_top_movers_sp500(123) is None


def test_get_top_movers_sp500_down() -> None:
    with patch("robin_stocks.robinhood.markets.request_get", return_value=[{"symbol": "AAPL"}]) as rg:
        markets.get_top_movers_sp500("down")
    assert rg.call_args[0][2] == {"direction": "down"}


def test_get_all_stocks_from_market_tag_returns_quotes() -> None:
    with (
        patch("robin_stocks.robinhood.markets.request_get", return_value={"instruments": ["url1"]}),
        patch("robin_stocks.robinhood.markets.get_symbol_by_url", return_value="AAPL"),
        patch("robin_stocks.robinhood.markets.get_quotes", return_value=[{"symbol": "AAPL"}]) as gq,
    ):
        out = markets.get_all_stocks_from_market_tag("technology")
    gq.assert_called_once()
    assert out == [{"symbol": "AAPL"}]


def test_get_all_stocks_from_market_tag_invalid_tag_returns_none() -> None:
    with patch("robin_stocks.robinhood.markets.request_get", return_value={"instruments": []}):
        out = markets.get_all_stocks_from_market_tag("notatag")
    assert out == [None]


def test_get_market_today_hours_resolves_market() -> None:
    with (
        patch(
            "robin_stocks.robinhood.markets.get_markets", return_value=[{"mic": "XNYS", "todays_hours": "https://x/hours/"}]
        ),
        patch("robin_stocks.robinhood.markets.request_get", return_value={"opens_at": "9:30"}),
    ):
        out = markets.get_market_today_hours("XNYS")
    assert out == {"opens_at": "9:30"}


def test_get_market_today_hours_invalid_market_raises() -> None:
    with patch("robin_stocks.robinhood.markets.get_markets", return_value=[{"mic": "XNYS", "todays_hours": "url"}]):
        with pytest.raises(Exception, match="Not a valid market name"):
            markets.get_market_today_hours("BOGUS")


def test_get_market_next_open_hours_resolves_market() -> None:
    # get_market_next_open_hours delegates to get_market_today_hours for the URL
    with (
        patch("robin_stocks.robinhood.markets.get_market_today_hours", return_value="https://x/next/"),
        patch("robin_stocks.robinhood.markets.request_get", return_value={"opens_at": "9:30"}),
    ):
        out = markets.get_market_next_open_hours("XNYS")
    assert out == {"opens_at": "9:30"}


def test_get_market_next_open_hours_after_date_resolves() -> None:
    with (
        patch("robin_stocks.robinhood.markets.get_market_hours", return_value={"next_open_hours": "https://x/after/"}),
        patch("robin_stocks.robinhood.markets.request_get", return_value={"opens_at": "9:30"}),
    ):
        out = markets.get_market_next_open_hours_after_date("XNYS", "2026-05-22")
    assert out == {"opens_at": "9:30"}


def test_get_top_100_returns_quotes() -> None:
    with (
        patch("robin_stocks.robinhood.markets.request_get", return_value={"instruments": ["url1"]}),
        patch("robin_stocks.robinhood.markets.get_symbol_by_url", return_value="AAPL"),
        patch("robin_stocks.robinhood.markets.get_quotes", return_value=[{"symbol": "AAPL"}]),
    ):
        out = markets.get_top_100()
    assert out == [{"symbol": "AAPL"}]


def test_get_top_movers_returns_quotes() -> None:
    with (
        patch("robin_stocks.robinhood.markets.request_get", return_value={"instruments": ["url1"]}),
        patch("robin_stocks.robinhood.markets.get_symbol_by_url", return_value="AAPL"),
        patch("robin_stocks.robinhood.markets.get_quotes", return_value=[{"symbol": "AAPL"}]),
    ):
        out = markets.get_top_movers()
    assert out == [{"symbol": "AAPL"}]
