"""Order-placement tests with mocked HTTP.

Focuses on the behavioral changes from PR #454 (market_hours coupling) and the
fork-only order_sell_tax_lot. Mocks the SDK plumbing (request_post,
load_account_profile, get_instruments_by_symbols, get_latest_price) and asserts
on the payload that would be sent to Robinhood.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import orders


@pytest.fixture
def mocked_order_deps():
    """Mock every external dependency of order() / order_sell_tax_lot."""
    patches = [
        patch("robin_stocks.robinhood.orders.request_post", return_value={"id": "ord-1"}),
        patch("robin_stocks.robinhood.orders.load_account_profile", return_value="https://api.robinhood.com/accounts/acct/"),
        patch(
            "robin_stocks.robinhood.orders.get_instruments_by_symbols",
            return_value=[{"id": "inst-1", "url": "https://api.robinhood.com/instruments/inst-1/"}],
        ),
        patch("robin_stocks.robinhood.orders.get_latest_price", return_value=["100.00"]),
        # login_required decorator
        patch("robin_stocks.robinhood.helper.LOGGED_IN", True),
    ]
    entered = [p.__enter__() for p in patches]
    yield {"request_post": entered[0]}
    for p in patches:
        p.__exit__(None, None, None)


# ---------------------------------------------------------------------------
# market_hours auto-upgrade (PR #454)
# ---------------------------------------------------------------------------


def test_order_with_extended_hours_true_and_regular_hours_upgrades_market_hours(mocked_order_deps) -> None:
    """The smoking-gun test for #454: setting extendedHours=True must
    auto-upgrade market_hours to 'extended_hours'. Before #454, the order
    payload kept market_hours='regular_hours' and the extended-hours flag
    was silently ignored by Robinhood's matching engine."""
    orders.order(
        "AAPL",
        1,
        "buy",
        extendedHours=True,
        market_hours="regular_hours",
    )
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["market_hours"] == "extended_hours"
    assert payload["extended_hours"] is True


def test_order_with_extended_hours_false_keeps_regular_hours(mocked_order_deps) -> None:
    """No auto-upgrade when extendedHours is False."""
    orders.order(
        "AAPL",
        1,
        "buy",
        extendedHours=False,
        market_hours="regular_hours",
    )
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["market_hours"] == "regular_hours"
    assert payload["extended_hours"] is False


def test_order_with_extended_hours_true_and_already_extended_no_change(mocked_order_deps) -> None:
    """If the caller already set market_hours='extended_hours', leave it alone."""
    orders.order(
        "AAPL",
        1,
        "buy",
        extendedHours=True,
        market_hours="extended_hours",
    )
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["market_hours"] == "extended_hours"


def test_order_with_extended_hours_true_and_all_day_hours_no_change(mocked_order_deps) -> None:
    """all_day_hours should not be downgraded just because extendedHours=True."""
    orders.order(
        "AAPL",
        1,
        "buy",
        extendedHours=True,
        market_hours="all_day_hours",
    )
    payload = mocked_order_deps["request_post"].call_args[0][1]
    # Must not be reset to extended_hours — only regular_hours triggers the upgrade
    assert payload["market_hours"] == "all_day_hours"


# ---------------------------------------------------------------------------
# Payload shape — verify nothing in order() regressed
# ---------------------------------------------------------------------------


def test_order_market_buy_payload_keys(mocked_order_deps) -> None:
    orders.order("AAPL", 1, "buy")
    payload = mocked_order_deps["request_post"].call_args[0][1]
    expected = {
        "account",
        "instrument",
        "symbol",
        "price",
        "ask_price",
        "bid_ask_timestamp",
        "bid_price",
        "quantity",
        "ref_id",
        "type",
        "time_in_force",
        "trigger",
        "side",
        "market_hours",
        "extended_hours",
        "order_form_version",
    }
    assert expected.issubset(payload.keys())
    # Market orders without stop don't carry stop_price
    assert "stop_price" not in payload


def test_order_with_stop_price_keeps_stop_price(mocked_order_deps) -> None:
    orders.order("AAPL", 1, "buy", stopPrice=100.0)
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["stop_price"] == 100.0
    assert payload["trigger"] == "stop"


def test_order_buy_market_uses_ask_price_branch(mocked_order_deps) -> None:
    orders.order("AAPL", 1, "buy")
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["side"] == "buy"


def test_order_sell_market_uses_bid_price_branch(mocked_order_deps) -> None:
    orders.order("AAPL", 1, "sell")
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["side"] == "sell"


def test_order_invalid_symbol_returns_none(mocked_order_deps) -> None:
    """A non-string symbol should be rejected before any network call."""
    out = orders.order(None, 1, "buy")
    assert out is None


# ---------------------------------------------------------------------------
# order_sell_tax_lot — fork-only "Sell by Lot" flow
# ---------------------------------------------------------------------------


def test_order_sell_tax_lot_rejects_empty_lots(mocked_order_deps) -> None:
    out = orders.order_sell_tax_lot("AAPL", lots=[])
    assert out is None
    mocked_order_deps["request_post"].assert_not_called()


def test_order_sell_tax_lot_rejects_missing_keys(mocked_order_deps) -> None:
    out = orders.order_sell_tax_lot("AAPL", lots=[{"open_lot_id": "L1"}])  # no 'quantity'
    assert out is None


def test_order_sell_tax_lot_rejects_non_string_symbol(mocked_order_deps) -> None:
    """Integers etc. have no .upper()."""
    out = orders.order_sell_tax_lot(None, lots=[{"open_lot_id": "L1", "quantity": "1"}])
    assert out is None


def test_order_sell_tax_lot_payload_has_required_keys(mocked_order_deps) -> None:
    out = orders.order_sell_tax_lot(
        "AAPL",
        lots=[
            {"open_lot_id": "L1", "quantity": "1"},
            {"open_lot_id": "L2", "quantity": "2"},
        ],
    )
    payload = mocked_order_deps["request_post"].call_args[0][1]

    assert payload["symbol"] == "AAPL"
    assert payload["side"] == "sell"
    assert payload["type"] == "market"
    assert payload["tax_lot_selection_type"] == "custom"
    assert payload["position_effect"] == "close"
    assert payload["order_form_version"] == 7
    # Total quantity is the sum of the lot quantities (as a Decimal-as-str)
    assert payload["quantity"] == "3"
    # Each lot's quantity is normalized to a string
    assert payload["tax_lots"] == [
        {"open_lot_id": "L1", "quantity": "1"},
        {"open_lot_id": "L2", "quantity": "2"},
    ]
    # ID returned by request_post mock should bubble up
    assert out == {"id": "ord-1"}


def test_order_sell_tax_lot_uppercase_normalizes_symbol(mocked_order_deps) -> None:
    orders.order_sell_tax_lot("  aapl ", lots=[{"open_lot_id": "L1", "quantity": "1"}])
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["symbol"] == "AAPL"


def test_order_sell_tax_lot_market_hours_upgrade_when_extended_hours(mocked_order_deps) -> None:
    """PR #454 audit: tax-lot order must also upgrade market_hours."""
    orders.order_sell_tax_lot(
        "AAPL",
        lots=[{"open_lot_id": "L1", "quantity": "1"}],
        extendedHours=True,
        market_hours="regular_hours",
    )
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["market_hours"] == "extended_hours"
    assert payload["extended_hours"] is True


def test_order_sell_tax_lot_handles_fractional_quantities(mocked_order_deps) -> None:
    """Quantities like '0.5' must be accepted and summed correctly."""
    orders.order_sell_tax_lot(
        "AAPL",
        lots=[
            {"open_lot_id": "L1", "quantity": "0.5"},
            {"open_lot_id": "L2", "quantity": "1.25"},
        ],
    )
    payload = mocked_order_deps["request_post"].call_args[0][1]
    assert payload["quantity"] == "1.75"


def test_order_sell_tax_lot_rejects_garbage_quantity(mocked_order_deps) -> None:
    out = orders.order_sell_tax_lot(
        "AAPL",
        lots=[{"open_lot_id": "L1", "quantity": "abc"}],
    )
    assert out is None
