"""Tests for robin_stocks.robinhood.ipo — IPO Access view models and orders."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import ipo, urls


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ---------------------------------------------------------------------------
# URL builders
# ---------------------------------------------------------------------------


def test_ipo_access_list_url() -> None:
    assert urls.ipo_access_list_url() == "https://bonfire.robinhood.com/lists/ipo_access/view_model/"


def test_ipo_access_cards_url_accepts_a_single_id() -> None:
    """A bare string must not be joined character by character."""
    assert urls.ipo_access_cards_url("abc-123") == "https://bonfire.robinhood.com/lists/ipo_access/cards/?ids=abc-123"


def test_ipo_access_cards_url_joins_multiple_ids() -> None:
    assert urls.ipo_access_cards_url(["a", "b"]) == "https://bonfire.robinhood.com/lists/ipo_access/cards/?ids=a,b"


def test_ipo_access_summary_url() -> None:
    assert (
        urls.ipo_access_summary_url("i1") == "https://bonfire.robinhood.com/equity_trading/ipo_access/viewmodels/summary/i1/"
    )


def test_ipo_access_order_entry_url_without_account() -> None:
    assert (
        urls.ipo_access_order_entry_url("i1")
        == "https://bonfire.robinhood.com/equity_trading/ipo_access/viewmodels/web_order_entry/i1/"
    )


def test_ipo_access_order_entry_url_with_account() -> None:
    assert urls.ipo_access_order_entry_url("i1", "ACC1").endswith("/web_order_entry/i1/?account_number=ACC1")


def test_ipo_access_allocation_results_url() -> None:
    assert urls.ipo_access_allocation_results_url("i1").endswith("/viewmodels/allocation_results/i1/")


def test_ipo_access_trade_receipt_url() -> None:
    assert urls.ipo_access_trade_receipt_url("o1").endswith("/viewmodels/trade_receipt/o1/")


# ---------------------------------------------------------------------------
# View-model getters
# ---------------------------------------------------------------------------

EMPTY_LIST_VIEW_MODEL = {
    "empty_state": {"title": "No new IPOs available", "subtitle_markdown": "This list gets updated..."},
    "learn_tab": {"sections": []},
}


def test_get_ipo_access_list_returns_the_view_model() -> None:
    with patch("robin_stocks.robinhood.ipo.request_get", return_value=EMPTY_LIST_VIEW_MODEL) as rg:
        out = ipo.get_ipo_access_list()
    assert rg.call_args[0][0] == urls.ipo_access_list_url()
    assert out["empty_state"]["title"] == "No new IPOs available"


def test_get_ipo_access_list_filters_with_info() -> None:
    with patch("robin_stocks.robinhood.ipo.request_get", return_value=EMPTY_LIST_VIEW_MODEL):
        assert ipo.get_ipo_access_list(info="empty_state") == EMPTY_LIST_VIEW_MODEL["empty_state"]


def test_get_ipo_access_cards_requests_results() -> None:
    with patch("robin_stocks.robinhood.ipo.request_get", return_value=[{"instrument_id": "i1"}]) as rg:
        out = ipo.get_ipo_access_cards(["i1", "i2"])
    assert rg.call_args[0][0].endswith("?ids=i1,i2")
    assert rg.call_args[0][1] == "results"
    assert out == [{"instrument_id": "i1"}]


def test_get_ipo_access_summary_hits_the_instrument_endpoint() -> None:
    with patch("robin_stocks.robinhood.ipo.request_get", return_value={"instrument_id": "i1"}) as rg:
        ipo.get_ipo_access_summary("i1")
    assert rg.call_args[0][0] == urls.ipo_access_summary_url("i1")


def test_get_ipo_access_order_entry_passes_the_account_number() -> None:
    view_model = {"instrument_id": "i1", "context": {"user_is_eligible": True}}
    with patch("robin_stocks.robinhood.ipo.request_get", return_value=view_model) as rg:
        out = ipo.get_ipo_access_order_entry("i1", account_number="ACC1")
    assert "account_number=ACC1" in rg.call_args[0][0]
    assert out["context"]["user_is_eligible"] is True


def test_get_ipo_access_allocation_results() -> None:
    with patch("robin_stocks.robinhood.ipo.request_get", return_value={"shares": "5"}) as rg:
        assert ipo.get_ipo_access_allocation_results("i1") == {"shares": "5"}
    assert rg.call_args[0][0] == urls.ipo_access_allocation_results_url("i1")


def test_get_ipo_access_trade_receipt() -> None:
    with patch("robin_stocks.robinhood.ipo.request_get", return_value={"id": "o1"}) as rg:
        assert ipo.get_ipo_access_trade_receipt("o1") == {"id": "o1"}
    assert rg.call_args[0][0] == urls.ipo_access_trade_receipt_url("o1")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


def test_get_ipo_access_orders_keeps_only_ipo_access_orders() -> None:
    orders = [
        {"id": "1", "is_ipo_access_order": True},
        {"id": "2", "is_ipo_access_order": False},
        {"id": "3"},
    ]
    with patch("robin_stocks.robinhood.ipo.get_all_stock_orders", return_value=orders):
        assert ipo.get_ipo_access_orders() == [{"id": "1", "is_ipo_access_order": True}]


def test_get_ipo_access_orders_survives_a_none_row() -> None:
    """get_all_stock_orders returns [None] when the request fails."""
    with patch("robin_stocks.robinhood.ipo.get_all_stock_orders", return_value=[None]):
        assert ipo.get_ipo_access_orders() == []


def test_get_ipo_access_orders_filters_with_info() -> None:
    orders = [{"id": "1", "is_ipo_access_order": True}]
    with patch("robin_stocks.robinhood.ipo.get_all_stock_orders", return_value=orders):
        assert ipo.get_ipo_access_orders(info="id") == ["1"]
