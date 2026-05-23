"""Sweep tests for the option-order and crypto-order helpers in orders.py.

Mocks request_post + the id/account lookups and asserts the payload's leg
structure and side. Includes order_sell_option_limit_by_id (PR #361).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import orders


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


@pytest.fixture
def opt_deps():
    patches = [
        patch("robin_stocks.robinhood.orders.request_post", return_value={"id": "ord"}),
        patch("robin_stocks.robinhood.orders.load_account_profile", return_value="https://api/accounts/acct/"),
        patch("robin_stocks.robinhood.orders.id_for_option", return_value="opt-1"),
        patch("robin_stocks.robinhood.orders.option_instruments_url", return_value="https://api/options/instruments/opt-1/"),
    ]
    entered = [p.__enter__() for p in patches]
    yield {"request_post": entered[0], "load_account_profile": entered[1]}
    for p in patches:
        p.__exit__(None, None, None)


# ---------------------------------------------------------------------------
# Single-leg option limit orders
# ---------------------------------------------------------------------------


def test_order_buy_option_limit_builds_buy_leg(opt_deps) -> None:
    orders.order_buy_option_limit("open", "debit", 1.00, "AAPL", 1, "2026-06-19", 150, "call")
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["direction"] == "debit"
    assert payload["legs"][0]["side"] == "buy"
    assert payload["legs"][0]["position_effect"] == "open"
    assert payload["type"] == "limit"


def test_order_sell_option_limit_builds_sell_leg(opt_deps) -> None:
    orders.order_sell_option_limit("close", "credit", 1.00, "AAPL", 1, "2026-06-19", 150, "call")
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["legs"][0]["side"] == "sell"
    assert payload["direction"] == "credit"


def test_order_sell_option_limit_by_id_builds_sell_leg(opt_deps) -> None:
    """PR #361: the by-id variant skips id_for_option and uses optionID directly."""
    orders.order_sell_option_limit_by_id("close", "credit", 1.00, 1, "opt-direct")
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["legs"][0]["side"] == "sell"
    assert payload["price"] == 1.00
    assert payload["quantity"] == 1


def test_order_buy_option_stop_limit_has_stop_trigger(opt_deps) -> None:
    orders.order_buy_option_stop_limit("open", "debit", 1.00, 0.90, "AAPL", 1, "2026-06-19", 150, "call")
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["trigger"] == "stop"
    assert payload["legs"][0]["side"] == "buy"


def test_order_sell_option_stop_limit_has_stop_trigger(opt_deps) -> None:
    orders.order_sell_option_stop_limit("close", "credit", 1.00, 1.10, "AAPL", 1, "2026-06-19", 150, "call")
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["trigger"] == "stop"
    assert payload["legs"][0]["side"] == "sell"


def test_order_buy_option_limit_invalid_symbol_returns_none(opt_deps) -> None:
    out = orders.order_buy_option_limit("open", "debit", 1.00, None, 1, "2026-06-19", 150, "call")
    assert out is None


# ---------------------------------------------------------------------------
# Spreads
# ---------------------------------------------------------------------------


def test_order_option_credit_spread_uses_credit_direction(opt_deps) -> None:
    spread = [
        {
            "expirationDate": "2026-06-19",
            "strike": 150,
            "optionType": "call",
            "effect": "open",
            "action": "sell",
            "ratio_quantity": 1,
        }
    ]
    orders.order_option_credit_spread(1.00, "AAPL", 1, spread)
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["direction"] == "credit"


def test_order_option_debit_spread_uses_debit_direction(opt_deps) -> None:
    spread = [
        {
            "expirationDate": "2026-06-19",
            "strike": 150,
            "optionType": "call",
            "effect": "open",
            "action": "buy",
            "ratio_quantity": 1,
        }
    ]
    orders.order_option_debit_spread(1.00, "AAPL", 1, spread)
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["direction"] == "debit"


def test_order_option_credit_spread_does_not_swap_tif_and_account(opt_deps) -> None:
    """Regression: timeInForce and account_number must not be positionally swapped
    when forwarding to order_option_spread (whose signature orders account_number first)."""
    spread = [
        {
            "expirationDate": "2026-06-19",
            "strike": 150,
            "optionType": "call",
            "effect": "open",
            "action": "sell",
            "ratio_quantity": 1,
        }
    ]
    orders.order_option_credit_spread(1.00, "AAPL", 1, spread, timeInForce="gfd", account_number="ACC-9")
    payload = opt_deps["request_post"].call_args[0][1]
    assert payload["time_in_force"] == "gfd"
    assert opt_deps["load_account_profile"].call_args.kwargs.get("account_number") == "ACC-9"


def test_order_sell_option_stop_limit_requires_login(opt_deps) -> None:
    """Regression: order_sell_option_stop_limit was missing @login_required. With its
    internals mocked (opt_deps), an undecorated function would complete and return a
    payload while logged out; the decorator must short-circuit with a "logged in" error."""
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", False):
        with pytest.raises(Exception, match="logged in"):
            orders.order_sell_option_stop_limit("open", "debit", 1.0, 1.1, "AAPL", 1, "2026-06-19", 150, "call")


def test_order_option_spread_builds_legs(opt_deps) -> None:
    spread = [
        {
            "expirationDate": "2026-06-19",
            "strike": 150,
            "optionType": "call",
            "effect": "open",
            "action": "buy",
            "ratio_quantity": 1,
        },
        {
            "expirationDate": "2026-06-19",
            "strike": 160,
            "optionType": "call",
            "effect": "open",
            "action": "sell",
            "ratio_quantity": 1,
        },
    ]
    orders.order_option_spread("debit", 1.00, "AAPL", 1, spread)
    payload = opt_deps["request_post"].call_args[0][1]
    assert len(payload["legs"]) == 2


# ---------------------------------------------------------------------------
# Crypto orders
# ---------------------------------------------------------------------------


@pytest.fixture
def crypto_order_mock():
    with patch("robin_stocks.robinhood.orders.order_crypto", return_value={"id": "c-ord"}) as m:
        yield m


def test_order_buy_crypto_by_price_delegates(crypto_order_mock) -> None:
    orders.order_buy_crypto_by_price("BTC", 100.0)
    args = crypto_order_mock.call_args[0]
    assert args[0] == "BTC"
    assert args[1] == "buy"


def test_order_sell_crypto_by_price_delegates(crypto_order_mock) -> None:
    orders.order_sell_crypto_by_price("BTC", 100.0)
    args = crypto_order_mock.call_args[0]
    assert args[1] == "sell"


def test_order_buy_crypto_by_quantity_delegates(crypto_order_mock) -> None:
    orders.order_buy_crypto_by_quantity("BTC", 0.01)
    assert crypto_order_mock.call_args[0][1] == "buy"


def test_order_sell_crypto_by_quantity_delegates(crypto_order_mock) -> None:
    orders.order_sell_crypto_by_quantity("BTC", 0.01)
    assert crypto_order_mock.call_args[0][1] == "sell"


def test_order_buy_crypto_limit_delegates(crypto_order_mock) -> None:
    orders.order_buy_crypto_limit("BTC", 0.01, 50000)
    assert crypto_order_mock.call_args[0][1] == "buy"


def test_order_sell_crypto_limit_delegates(crypto_order_mock) -> None:
    orders.order_sell_crypto_limit("BTC", 0.01, 50000)
    assert crypto_order_mock.call_args[0][1] == "sell"


def test_order_buy_crypto_limit_by_price_delegates(crypto_order_mock) -> None:
    orders.order_buy_crypto_limit_by_price("BTC", 100.0, 50000)
    assert crypto_order_mock.call_args[0][1] == "buy"


def test_order_sell_crypto_limit_by_price_delegates(crypto_order_mock) -> None:
    orders.order_sell_crypto_limit_by_price("BTC", 100.0, 50000)
    assert crypto_order_mock.call_args[0][1] == "sell"


# ---------------------------------------------------------------------------
# order_crypto core
# ---------------------------------------------------------------------------


def test_order_crypto_builds_market_payload() -> None:
    with (
        patch("robin_stocks.robinhood.orders.request_post", return_value={"id": "c"}) as rp,
        patch("robin_stocks.robinhood.orders.load_crypto_profile", return_value={"id": "crypto-acct"}),
        patch(
            "robin_stocks.robinhood.orders.get_crypto_info",
            return_value={"id": "btc-id", "min_order_quantity_increment": "0.0001"},
        ),
        patch(
            "robin_stocks.robinhood.orders.get_crypto_quote",
            return_value={"mark_price": "50000", "ask_price": "50001", "bid_price": "49999"},
        ),
        patch("robin_stocks.robinhood.orders.round_price", side_effect=lambda x: x),
    ):
        orders.order_crypto("BTC", "buy", 0.01, amountIn="quantity")
    rp.assert_called_once()
    payload = rp.call_args[0][1]
    assert payload["side"] == "buy"
    assert payload["type"] == "market"


def test_order_crypto_invalid_symbol_returns_none() -> None:
    out = orders.order_crypto(None, "buy", 0.01)
    assert out is None
