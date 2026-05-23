"""URL builder tests — every public URL helper we touched.

These are pure functions, no network mocking needed.
"""

from __future__ import annotations

from robin_stocks.robinhood import urls

# ---------------------------------------------------------------------------
# Options (PR #432, #525, tax lots)
# ---------------------------------------------------------------------------


def test_option_positions_url_no_arg_returns_default_path() -> None:
    """PR #432: default account_number=None must produce the unfiltered endpoint."""
    assert urls.option_positions_url() == "https://api.robinhood.com/options/positions/"


def test_option_positions_url_with_account() -> None:
    assert urls.option_positions_url("ABC-123") == "https://api.robinhood.com/options/positions/?account_numbers=ABC-123"


def test_option_positions_url_with_keyword_arg() -> None:
    assert urls.option_positions_url(account_number="X") == "https://api.robinhood.com/options/positions/?account_numbers=X"


def test_option_orders_url_default() -> None:
    assert urls.option_orders_url() == "https://api.robinhood.com/options/orders/"


def test_option_orders_url_with_order_id() -> None:
    assert urls.option_orders_url(orderID="abc") == "https://api.robinhood.com/options/orders/abc/"


def test_option_orders_url_with_account_only() -> None:
    assert urls.option_orders_url(account_number="ACC") == "https://api.robinhood.com/options/orders/?account_numbers=ACC"


def test_option_orders_url_with_start_date_only() -> None:
    """PR #525: start_date should round-trip into the updated_at[gte] query."""
    assert (
        urls.option_orders_url(start_date="2026-01-01")
        == "https://api.robinhood.com/options/orders/?updated_at[gte]=2026-01-01"
    )


def test_option_orders_url_with_account_and_start_date_uses_and_separator() -> None:
    """Both filters must coexist; first becomes ?, second becomes &."""
    out = urls.option_orders_url(account_number="ACC", start_date="2026-01-01")
    assert out == ("https://api.robinhood.com/options/orders/?account_numbers=ACC&updated_at[gte]=2026-01-01")


def test_option_orders_url_with_all_three() -> None:
    out = urls.option_orders_url(orderID="ord", account_number="ACC", start_date="2026-01-01")
    assert out == ("https://api.robinhood.com/options/orders/ord/?account_numbers=ACC&updated_at[gte]=2026-01-01")


# ---------------------------------------------------------------------------
# Tax lots (fork-only)
# ---------------------------------------------------------------------------


def test_tax_lots_open_url() -> None:
    assert urls.tax_lots_open_url("ACC-123", "INST-456") == "https://api.robinhood.com/tax_lots/open/ACC-123/INST-456/"


def test_tax_lots_selected_url() -> None:
    assert urls.tax_lots_selected_url("order-xyz") == "https://api.robinhood.com/tax_lots/order/order-xyz/selected/"


def test_tax_lots_closed_url() -> None:
    assert urls.tax_lots_closed_url("order-xyz") == "https://api.robinhood.com/tax_lots/order/order-xyz/closed/"


# ---------------------------------------------------------------------------
# Marketdata (PR #541)
# ---------------------------------------------------------------------------


def test_marketdata_index_quotes_url() -> None:
    """PR #541: new endpoint for index option underlyings."""
    assert urls.marketdata_index_quotes_url("idx-id-1") == "https://api.robinhood.com/marketdata/indexes/values/v1/idx-id-1/"


def test_marketdata_quotes_url_unaffected_by_index_addition() -> None:
    """Regression: the regular stock-quotes URL must still resolve normally."""
    assert urls.marketdata_quotes_url("inst-1") == "https://api.robinhood.com/marketdata/quotes/inst-1/"


# ---------------------------------------------------------------------------
# Futures (PR #1641)
# ---------------------------------------------------------------------------


def test_futures_contract_url() -> None:
    assert urls.futures_contract_url("ESH26") == "https://api.robinhood.com/arsenal/v1/futures/contracts/symbol/ESH26"


def test_futures_contract_url_handles_special_characters() -> None:
    """Symbols are interpolated as-is; ensure trailing slash isn't added."""
    out = urls.futures_contract_url("NQM26")
    assert out.endswith("/NQM26")
    assert "//symbol" not in out


def test_futures_quotes_url() -> None:
    assert urls.futures_quotes_url() == "https://api.robinhood.com/marketdata/futures/quotes/v1/"


def test_futures_orders_url() -> None:
    assert urls.futures_orders_url("acct-uuid") == "https://api.robinhood.com/ceres/v1/accounts/acct-uuid/orders"


def test_futures_account_url() -> None:
    assert urls.futures_account_url() == "https://api.robinhood.com/ceres/v1/accounts/"


# ---------------------------------------------------------------------------
# Recurring investments (PR #1633)
# ---------------------------------------------------------------------------


def test_recurring_schedules_url_default() -> None:
    assert urls.recurring_schedules_url() == "https://bonfire.robinhood.com/recurring_schedules/"


def test_recurring_schedules_url_by_schedule_id_takes_priority() -> None:
    """schedule_id branch should win even when account_number is also passed."""
    out = urls.recurring_schedules_url(schedule_id="sched-1", account_number="should-be-ignored")
    assert out == "https://bonfire.robinhood.com/recurring_schedules/sched-1/"


def test_recurring_schedules_url_by_account_number() -> None:
    out = urls.recurring_schedules_url(account_number="ACC-1")
    assert out == ("https://bonfire.robinhood.com/recurring_schedules/?account_number=ACC-1")


def test_recurring_schedules_url_with_asset_types_list() -> None:
    out = urls.recurring_schedules_url(asset_types=["equity", "crypto"])
    assert out == ("https://bonfire.robinhood.com/recurring_schedules/?asset_types=equity&asset_types=crypto")


def test_recurring_schedules_url_with_single_asset_type_string() -> None:
    """A plain string should be coerced into a single-element list."""
    out = urls.recurring_schedules_url(asset_types="equity")
    assert out == ("https://bonfire.robinhood.com/recurring_schedules/?asset_types=equity")


def test_recurring_schedules_url_asset_types_wins_over_account_number() -> None:
    """When both are passed, asset_types takes priority (per the elif chain)."""
    out = urls.recurring_schedules_url(account_number="ACC-1", asset_types=["equity"])
    assert "asset_types=equity" in out
    assert "account_number" not in out


def test_next_investment_date_url() -> None:
    out = urls.next_investment_date_url("weekly", "2026-05-20")
    assert out == (
        "https://bonfire.robinhood.com/recurring_schedules/equity/next_investment_date/?frequency=weekly&start_date=2026-05-20"
    )


def test_next_investment_date_url_with_monthly_frequency() -> None:
    out = urls.next_investment_date_url("monthly", "2026-06-01")
    assert "frequency=monthly" in out
    assert "start_date=2026-06-01" in out
