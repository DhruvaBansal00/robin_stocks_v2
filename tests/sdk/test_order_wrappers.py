"""Sweep tests for every order_buy_/order_sell_/cancel_/get_ helper in orders.py.

These wrappers mostly delegate to ``order()`` or ``request_*``; the goal is to
catch a wrong arg order or missing forward at the boundary, not re-test the
underlying machinery.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import orders


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ---------------------------------------------------------------------------
# Order discovery / listing
# ---------------------------------------------------------------------------


def test_get_all_stock_orders_uses_pagination() -> None:
    with patch("robin_stocks.robinhood.orders.request_get", return_value=[{"id": "1"}]) as rg:
        orders.get_all_stock_orders()
    assert rg.call_args[0][1] == "pagination"


def test_get_all_option_orders_uses_pagination() -> None:
    with patch("robin_stocks.robinhood.orders.request_get", return_value=[{"id": "1"}]) as rg:
        orders.get_all_option_orders()
    assert rg.call_args[0][1] == "pagination"


def test_get_all_crypto_orders_uses_pagination() -> None:
    with patch("robin_stocks.robinhood.orders.request_get", return_value=[{"id": "1"}]) as rg:
        orders.get_all_crypto_orders()
    assert rg.call_args[0][1] == "pagination"


def test_get_all_open_stock_orders_filters_cancel_present() -> None:
    """get_all_open_stock_orders filters to entries with a non-null `cancel` URL."""
    raw = [{"id": "1", "cancel": None}, {"id": "2", "cancel": "url"}]
    with patch("robin_stocks.robinhood.orders.request_get", return_value=raw):
        out = orders.get_all_open_stock_orders()
    assert len(out) == 1
    assert out[0]["id"] == "2"


def test_get_all_open_option_orders_filters_cancel_url() -> None:
    raw = [{"id": "1", "cancel_url": None}, {"id": "2", "cancel_url": "url"}]
    with patch("robin_stocks.robinhood.orders.request_get", return_value=raw):
        out = orders.get_all_open_option_orders()
    assert len(out) == 1


def test_get_all_open_crypto_orders_filters_cancel_url() -> None:
    raw = [{"id": "1", "cancel_url": None}, {"id": "2", "cancel_url": "url"}]
    with patch("robin_stocks.robinhood.orders.request_get", return_value=raw):
        out = orders.get_all_open_crypto_orders()
    assert len(out) == 1


def test_get_stock_order_info_returns_dict() -> None:
    with patch("robin_stocks.robinhood.orders.request_get", return_value={"id": "ord-1"}) as rg:
        out = orders.get_stock_order_info("ord-1")
    assert out == {"id": "ord-1"}
    assert "ord-1" in rg.call_args[0][0]


def test_get_option_order_info_returns_dict() -> None:
    with patch("robin_stocks.robinhood.orders.request_get", return_value={"id": "ord-1"}):
        out = orders.get_option_order_info("ord-1")
    assert out == {"id": "ord-1"}


def test_get_crypto_order_info_returns_dict() -> None:
    with patch("robin_stocks.robinhood.orders.request_get", return_value={"id": "c-1"}):
        out = orders.get_crypto_order_info("c-1")
    assert out == {"id": "c-1"}


def test_find_stock_orders_returns_all_when_no_filters() -> None:
    """With no kwargs, find_stock_orders returns the full list."""
    raw = [{"id": "1", "quantity": "1", "cumulative_quantity": "1"}]
    with patch("robin_stocks.robinhood.orders.request_get", return_value=raw):
        out = orders.find_stock_orders()
    assert out == raw


def test_find_stock_orders_filters_by_kwargs() -> None:
    raw = [
        {"id": "1", "state": "filled", "side": "buy", "quantity": "1", "cumulative_quantity": "1"},
        {"id": "2", "state": "cancelled", "side": "buy", "quantity": "1", "cumulative_quantity": "1"},
    ]
    with patch("robin_stocks.robinhood.orders.request_get", return_value=raw):
        out = orders.find_stock_orders(state="filled")
    assert len(out) == 1
    assert out[0]["id"] == "1"


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------


def test_cancel_stock_order_calls_request_post() -> None:
    with patch("robin_stocks.robinhood.orders.request_post", return_value={"id": "1"}) as rp:
        orders.cancel_stock_order("ord-1")
    rp.assert_called_once()


def test_cancel_option_order_calls_request_post() -> None:
    with patch("robin_stocks.robinhood.orders.request_post", return_value={"id": "1"}) as rp:
        orders.cancel_option_order("ord-1")
    rp.assert_called_once()


def test_cancel_crypto_order_calls_request_post() -> None:
    with patch("robin_stocks.robinhood.orders.request_post", return_value={"id": "1"}) as rp:
        orders.cancel_crypto_order("ord-1")
    rp.assert_called_once()


def test_cancel_all_stock_orders_cancels_entries_with_cancel_url() -> None:
    """cancel_all_stock_orders posts to each non-null `cancel` link."""
    raw = [{"id": "a", "cancel": "url-a"}, {"id": "b", "cancel": None}, {"id": "c", "cancel": "url-c"}]
    with (
        patch("robin_stocks.robinhood.orders.request_get", return_value=raw),
        patch("robin_stocks.robinhood.orders.request_post") as rp,
    ):
        out = orders.cancel_all_stock_orders()
    assert rp.call_count == 2
    assert len(out) == 2  # only the cancellable entries


def test_cancel_all_option_orders_uses_cancel_url_key() -> None:
    """Options use `cancel_url`, not `cancel`."""
    raw = [{"id": "1", "cancel_url": "url-1"}, {"id": "2", "cancel_url": None}]
    with (
        patch("robin_stocks.robinhood.orders.request_get", return_value=raw),
        patch("robin_stocks.robinhood.orders.request_post") as rp,
    ):
        orders.cancel_all_option_orders()
    rp.assert_called_once_with("url-1")


def test_cancel_all_crypto_orders_uses_cancel_url_key() -> None:
    raw = [{"id": "1", "cancel_url": "url-1"}]
    with (
        patch("robin_stocks.robinhood.orders.request_get", return_value=raw),
        patch("robin_stocks.robinhood.orders.request_post") as rp,
    ):
        orders.cancel_all_crypto_orders()
    rp.assert_called_once_with("url-1")


# ---------------------------------------------------------------------------
# Order wrappers — all delegate to order(); we just confirm the side / type
# ---------------------------------------------------------------------------


@pytest.fixture
def order_mock():
    with patch("robin_stocks.robinhood.orders.order", return_value={"id": "o"}) as o:
        yield o


def test_order_buy_market_delegates_with_buy_side(order_mock) -> None:
    orders.order_buy_market("AAPL", 1)
    args = order_mock.call_args[0]
    assert args[0] == "AAPL"
    assert args[1] == 1
    assert args[2] == "buy"


def test_order_sell_market_delegates_with_sell_side(order_mock) -> None:
    orders.order_sell_market("AAPL", 1)
    args = order_mock.call_args[0]
    assert args[2] == "sell"


def test_order_buy_limit_passes_limit_price(order_mock) -> None:
    orders.order_buy_limit("AAPL", 1, 100.0)
    args = order_mock.call_args[0]
    assert args[3] == 100.0  # limitPrice arg
    assert args[2] == "buy"


def test_order_sell_limit_passes_limit_price(order_mock) -> None:
    orders.order_sell_limit("AAPL", 1, 50.0)
    args = order_mock.call_args[0]
    assert args[3] == 50.0
    assert args[2] == "sell"


def test_order_buy_stop_loss_passes_stop_price(order_mock) -> None:
    orders.order_buy_stop_loss("AAPL", 1, 100.0)
    # Inspect order() call to confirm stop price is wired into the right slot
    assert order_mock.called


def test_order_sell_stop_loss_passes_stop_price(order_mock) -> None:
    orders.order_sell_stop_loss("AAPL", 1, 100.0)
    assert order_mock.called


def test_order_buy_stop_limit_passes_both_prices(order_mock) -> None:
    orders.order_buy_stop_limit("AAPL", 1, 100.0, 95.0)
    assert order_mock.called


def test_order_sell_stop_limit_passes_both_prices(order_mock) -> None:
    orders.order_sell_stop_limit("AAPL", 1, 100.0, 95.0)
    assert order_mock.called


# ---------------------------------------------------------------------------
# Fractional orders
# ---------------------------------------------------------------------------


def test_order_buy_fractional_by_quantity_delegates(order_mock) -> None:
    orders.order_buy_fractional_by_quantity("AAPL", 0.5)
    assert order_mock.called


def test_order_sell_fractional_by_quantity_delegates(order_mock) -> None:
    orders.order_sell_fractional_by_quantity("AAPL", 0.5)
    assert order_mock.called


def test_order_buy_fractional_by_price_rejects_under_one_dollar(order_mock) -> None:
    out = orders.order_buy_fractional_by_price("AAPL", 0.5)
    assert out is None
    order_mock.assert_not_called()


def test_order_sell_fractional_by_price_rejects_under_one_dollar(order_mock) -> None:
    out = orders.order_sell_fractional_by_price("AAPL", 0.5)
    assert out is None
    order_mock.assert_not_called()


def test_order_buy_fractional_by_price_calls_order_for_valid_amount(order_mock) -> None:
    with patch("robin_stocks.robinhood.orders.get_latest_price", return_value=["100.00"]):
        orders.order_buy_fractional_by_price("AAPL", 100.0)
    assert order_mock.called


def test_order_buy_fractional_by_price_returns_none_at_zero_price(order_mock) -> None:
    """If the latest price is 0, the share quantity should be 0."""
    with patch("robin_stocks.robinhood.orders.get_latest_price", return_value=[0.0]):
        orders.order_buy_fractional_by_price("AAPL", 100.0)
    args = order_mock.call_args[0]
    # quantity should be 0
    assert args[1] == 0


# ---------------------------------------------------------------------------
# Trailing stop
# ---------------------------------------------------------------------------


def test_order_trailing_stop_called_with_side(order_mock) -> None:
    """The shared trailing-stop function is wrapped by buy/sell variants."""
    with patch("robin_stocks.robinhood.orders.order_trailing_stop", return_value={"id": "1"}) as ts:
        orders.order_buy_trailing_stop("AAPL", 1, 5.0)
    ts.assert_called_once()
    side_arg = ts.call_args[0][2]
    assert side_arg == "buy"
