"""Full coverage tests for robin_stocks.robinhood.futures (PR #1641).

Covers contract lookup, quote shape, multi-symbol payloads, cursor-based
pagination, order info lookup, P&L extraction (including the `_extract_amount`
edge cases), and account discovery.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import futures


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ---------------------------------------------------------------------------
# Contract functions
# ---------------------------------------------------------------------------


def test_get_futures_contract_returns_result_payload() -> None:
    with patch("robin_stocks.robinhood.futures.request_get", return_value={"result": {"id": "C1", "symbol": "/ESH26"}}) as rg, \
         patch("robin_stocks.robinhood.futures.update_session_for_futures") as upd:
        out = futures.get_futures_contract("esh26")

    rg.assert_called_once()
    upd.assert_called_once()
    assert out == {"id": "C1", "symbol": "/ESH26"}


def test_get_futures_contract_uppercase_normalization() -> None:
    """The function must uppercase + strip the symbol before calling the URL builder."""
    with patch("robin_stocks.robinhood.futures.request_get", return_value={"result": {"id": "C1"}}), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"), \
         patch("robin_stocks.robinhood.futures.futures_contract_url") as fcu:
        fcu.return_value = "https://example/"
        futures.get_futures_contract("  esh26  ")
        fcu.assert_called_once_with("ESH26")


def test_get_futures_contract_no_result_returns_none() -> None:
    with patch("robin_stocks.robinhood.futures.request_get", return_value={"detail": "not found"}), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_contract("FAKE") is None


def test_get_futures_contract_none_response_returns_none() -> None:
    with patch("robin_stocks.robinhood.futures.request_get", return_value=None), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_contract("FAKE") is None


def test_get_futures_contract_info_filter() -> None:
    with patch("robin_stocks.robinhood.futures.request_get", return_value={"result": {"id": "C1", "multiplier": "50"}}), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_contract("ESH26", info="multiplier") == "50"


def test_get_futures_contracts_by_symbols_accepts_string() -> None:
    """A bare string should be coerced into a single-element list."""
    with patch("robin_stocks.robinhood.futures.get_futures_contract", return_value={"id": "C1"}) as gc:
        out = futures.get_futures_contracts_by_symbols("ESH26")
    gc.assert_called_once_with("ESH26", info=None)
    assert out == [{"id": "C1"}]


def test_get_futures_contracts_by_symbols_skips_nulls() -> None:
    """If a symbol returns None, it's filtered out of the response."""
    with patch(
        "robin_stocks.robinhood.futures.get_futures_contract",
        side_effect=[{"id": "A"}, None, {"id": "B"}],
    ):
        out = futures.get_futures_contracts_by_symbols(["A", "B", "C"])
    assert len(out) == 2
    assert out == [{"id": "A"}, {"id": "B"}]


def test_get_futures_contracts_by_symbols_empty_list() -> None:
    out = futures.get_futures_contracts_by_symbols([])
    assert out == []


# ---------------------------------------------------------------------------
# Quote functions
# ---------------------------------------------------------------------------


def test_get_futures_quote_resolves_symbol_then_fetches() -> None:
    with patch("robin_stocks.robinhood.futures.id_for_futures_contract", return_value="cid-1") as idf, \
         patch("robin_stocks.robinhood.futures.get_futures_quote_by_id", return_value={"bid_price": "100"}) as gq:
        out = futures.get_futures_quote("ESH26", info=None)
    idf.assert_called_once_with("ESH26")
    gq.assert_called_once_with("cid-1", None)
    assert out == {"bid_price": "100"}


def test_get_futures_quote_returns_none_when_contract_not_found() -> None:
    with patch("robin_stocks.robinhood.futures.id_for_futures_contract", return_value=None):
        out = futures.get_futures_quote("FAKE")
    assert out is None


def test_get_futures_quote_by_id_unwraps_nested_data() -> None:
    """The quote endpoint returns {data: [{data: {...}}]}; we must unwrap one level."""
    body = {"data": [{"data": {"bid_price": "100.5", "ask_price": "100.6"}}]}
    with patch("robin_stocks.robinhood.futures.request_get", return_value=body), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        out = futures.get_futures_quote_by_id("cid-1")
    assert out == {"bid_price": "100.5", "ask_price": "100.6"}


def test_get_futures_quote_by_id_empty_data_returns_none() -> None:
    with patch("robin_stocks.robinhood.futures.request_get", return_value={"data": []}), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_quote_by_id("cid-1") is None


def test_get_futures_quote_by_id_missing_inner_data_returns_none() -> None:
    """If the outer item lacks 'data', the helper should not raise."""
    with patch("robin_stocks.robinhood.futures.request_get", return_value={"data": [{}]}), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_quote_by_id("cid-1") is None


def test_get_futures_quotes_multiple_symbols_joins_ids() -> None:
    """Quote API expects comma-separated ids in the payload."""
    with patch("robin_stocks.robinhood.futures.id_for_futures_contract", side_effect=["a-id", "b-id"]), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"), \
         patch("robin_stocks.robinhood.futures.request_get", return_value={"data": [{"data": {"x": 1}}, {"data": {"x": 2}}]}) as rg:
        out = futures.get_futures_quotes(["A", "B"])
    payload = rg.call_args[1]["payload"]
    assert payload["ids"] == "a-id,b-id"
    assert out == [{"x": 1}, {"x": 2}]


def test_get_futures_quotes_returns_empty_when_no_contracts_found() -> None:
    with patch("robin_stocks.robinhood.futures.id_for_futures_contract", return_value=None):
        out = futures.get_futures_quotes(["FAKE", "ALSO_FAKE"])
    assert out == []


def test_get_futures_quotes_accepts_single_string() -> None:
    """A single string symbol should be coerced into a list."""
    with patch("robin_stocks.robinhood.futures.id_for_futures_contract", return_value="cid-1"), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"), \
         patch("robin_stocks.robinhood.futures.request_get", return_value={"data": [{"data": {}}]}) as rg:
        futures.get_futures_quotes("ESH26")
    assert rg.call_args[1]["payload"]["ids"] == "cid-1"


def test_get_futures_quotes_request_failure_returns_empty() -> None:
    with patch("robin_stocks.robinhood.futures.id_for_futures_contract", return_value="cid-1"), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"), \
         patch("robin_stocks.robinhood.futures.request_get", return_value=None):
        out = futures.get_futures_quotes(["ESH26"])
    assert out == []


# ---------------------------------------------------------------------------
# Order pagination — cursor-based loop
# ---------------------------------------------------------------------------


def test_get_all_futures_orders_paginates_until_cursor_none() -> None:
    """Three-page response: pages with 'next', terminates when next is None."""
    page1 = {"results": [{"orderId": "1"}], "next": "cursor-2"}
    page2 = {"results": [{"orderId": "2"}], "next": "cursor-3"}
    page3 = {"results": [{"orderId": "3"}], "next": None}

    with patch(
        "robin_stocks.robinhood.futures.request_get",
        side_effect=[page1, page2, page3],
    ) as rg, patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        orders = futures.get_all_futures_orders(account_id="acct-1")

    assert [o["orderId"] for o in orders] == ["1", "2", "3"]
    # Confirm subsequent requests included the cursor
    payloads = [c.kwargs["payload"] for c in rg.call_args_list]
    assert payloads[0] == {"contractType": "OUTRIGHT"}
    assert payloads[1] == {"contractType": "OUTRIGHT", "cursor": "cursor-2"}
    assert payloads[2] == {"contractType": "OUTRIGHT", "cursor": "cursor-3"}


def test_get_all_futures_orders_terminates_on_missing_results_key() -> None:
    """A response without 'results' should break the loop instead of raising."""
    with patch(
        "robin_stocks.robinhood.futures.request_get",
        return_value={"detail": "no data"},
    ), patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        out = futures.get_all_futures_orders(account_id="acct-1")
    assert out == []


def test_get_all_futures_orders_terminates_on_none_response() -> None:
    with patch(
        "robin_stocks.robinhood.futures.request_get",
        return_value=None,
    ), patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        out = futures.get_all_futures_orders(account_id="acct-1")
    assert out == []


def test_get_all_futures_orders_auto_detects_account_id_when_missing() -> None:
    """If account_id is None, we should call get_futures_account_id."""
    with patch("robin_stocks.robinhood.futures.get_futures_account_id", return_value="resolved-acct") as gai, \
         patch("robin_stocks.robinhood.futures.request_get", return_value={"results": [], "next": None}), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        futures.get_all_futures_orders()
    gai.assert_called_once()


def test_get_all_futures_orders_returns_none_when_no_account_found() -> None:
    """If account discovery fails, we must abort cleanly."""
    with patch("robin_stocks.robinhood.futures.get_futures_account_id", return_value=None):
        out = futures.get_all_futures_orders()
    assert out is None


def test_get_filled_futures_orders_sends_filled_filter() -> None:
    """The filled-only helper must add orderState='FILLED' to each request."""
    with patch(
        "robin_stocks.robinhood.futures.request_get",
        return_value={"results": [{"orderId": "1", "orderState": "FILLED"}], "next": None},
    ) as rg, patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        futures.get_filled_futures_orders(account_id="acct-1")
    payload = rg.call_args[1]["payload"]
    assert payload["orderState"] == "FILLED"


def test_get_filled_futures_orders_auto_detects_account() -> None:
    with patch("robin_stocks.robinhood.futures.get_futures_account_id", return_value="auto-acct") as gai, \
         patch("robin_stocks.robinhood.futures.request_get", return_value={"results": [], "next": None}), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        futures.get_filled_futures_orders()
    gai.assert_called_once()


def test_get_filled_futures_orders_returns_none_when_no_account() -> None:
    with patch("robin_stocks.robinhood.futures.get_futures_account_id", return_value=None):
        assert futures.get_filled_futures_orders() is None


def test_get_filled_futures_orders_paginates_through_multiple_pages() -> None:
    """Exercises the cursor + page-increment branches of get_filled_futures_orders."""
    page1 = {"results": [{"orderId": "f1"}], "next": "cursor-2"}
    page2 = {"results": [{"orderId": "f2"}], "next": None}

    with patch(
        "robin_stocks.robinhood.futures.request_get",
        side_effect=[page1, page2],
    ) as rg, patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        out = futures.get_filled_futures_orders(account_id="acct-1")

    assert [o["orderId"] for o in out] == ["f1", "f2"]
    # Confirm the cursor was carried into page 2
    payloads = [c.kwargs["payload"] for c in rg.call_args_list]
    assert "cursor" not in payloads[0]
    assert payloads[1]["cursor"] == "cursor-2"


def test_get_filled_futures_orders_terminates_on_none_response() -> None:
    """The early-break path when request_get returns falsy (already covered for
    get_all_futures_orders; add the parallel test for get_filled_futures_orders)."""
    with patch("robin_stocks.robinhood.futures.request_get", return_value=None), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        out = futures.get_filled_futures_orders(account_id="acct-1")
    assert out == []


# ---------------------------------------------------------------------------
# get_futures_order_info — filters the all-orders result
# ---------------------------------------------------------------------------


def test_get_futures_order_info_returns_matching_order() -> None:
    with patch(
        "robin_stocks.robinhood.futures.get_all_futures_orders",
        return_value=[{"orderId": "a"}, {"orderId": "b"}, {"orderId": "c"}],
    ):
        out = futures.get_futures_order_info("b", account_id="acct-1")
    assert out == {"orderId": "b"}


def test_get_futures_order_info_returns_none_if_no_match() -> None:
    with patch(
        "robin_stocks.robinhood.futures.get_all_futures_orders",
        return_value=[{"orderId": "a"}],
    ):
        assert futures.get_futures_order_info("zzz") is None


def test_get_futures_order_info_returns_none_when_no_orders() -> None:
    with patch("robin_stocks.robinhood.futures.get_all_futures_orders", return_value=None):
        assert futures.get_futures_order_info("anything") is None


def test_get_futures_order_info_filters_by_info() -> None:
    with patch(
        "robin_stocks.robinhood.futures.get_all_futures_orders",
        return_value=[{"orderId": "b", "averagePrice": "100"}],
    ):
        out = futures.get_futures_order_info("b", info="averagePrice")
    assert out == "100"


# ---------------------------------------------------------------------------
# Account discovery
# ---------------------------------------------------------------------------


def test_get_futures_account_id_finds_futures_account() -> None:
    data = [
        {"accountType": "STOCK", "id": "stock-id"},
        {"accountType": "FUTURES", "id": "futures-id"},
    ]
    with patch("robin_stocks.robinhood.futures.request_get", return_value=data), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_account_id() == "futures-id"


def test_get_futures_account_id_returns_none_when_no_futures_account() -> None:
    data = [{"accountType": "STOCK", "id": "stock-id"}]
    with patch("robin_stocks.robinhood.futures.request_get", return_value=data), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_account_id() is None


def test_get_futures_account_id_returns_none_when_no_data() -> None:
    with patch("robin_stocks.robinhood.futures.request_get", return_value=None), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_account_id() is None


def test_get_futures_account_id_returns_none_when_empty_list() -> None:
    with patch("robin_stocks.robinhood.futures.request_get", return_value=[]), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_account_id() is None


def test_get_futures_account_id_ignores_non_dict_entries() -> None:
    """If the API ever returns mixed types, we shouldn't crash."""
    data = ["garbage", {"accountType": "FUTURES", "id": "futures-id"}]
    with patch("robin_stocks.robinhood.futures.request_get", return_value=data), \
         patch("robin_stocks.robinhood.futures.update_session_for_futures"):
        assert futures.get_futures_account_id() == "futures-id"


# ---------------------------------------------------------------------------
# get_futures_positions — placeholder
# ---------------------------------------------------------------------------


def test_get_futures_positions_returns_none_until_endpoint_discovered() -> None:
    """Placeholder — endpoint hasn't been reverse-engineered yet."""
    assert futures.get_futures_positions() is None


# ---------------------------------------------------------------------------
# _extract_amount — every branch
# ---------------------------------------------------------------------------


def test_extract_amount_none() -> None:
    assert futures._extract_amount(None) == 0.0


def test_extract_amount_int() -> None:
    assert futures._extract_amount(5) == 5.0


def test_extract_amount_float() -> None:
    assert futures._extract_amount(3.14) == 3.14


def test_extract_amount_numeric_string() -> None:
    assert futures._extract_amount("12.34") == 12.34


def test_extract_amount_empty_string() -> None:
    assert futures._extract_amount("") == 0.0


def test_extract_amount_dict_with_amount() -> None:
    assert futures._extract_amount({"amount": "100.50", "currency": "USD"}) == 100.50


def test_extract_amount_dict_with_empty_amount() -> None:
    assert futures._extract_amount({"amount": "", "currency": "USD"}) == 0.0


def test_extract_amount_dict_without_amount_key() -> None:
    """Missing 'amount' key falls through to the default 0.0 branch."""
    assert futures._extract_amount({"foo": "bar"}) == 0.0


def test_extract_amount_unknown_type() -> None:
    assert futures._extract_amount(object()) == 0.0


# ---------------------------------------------------------------------------
# extract_futures_pnl — branch coverage
# ---------------------------------------------------------------------------


def test_extract_futures_pnl_empty_order_returns_zeros() -> None:
    out = futures.extract_futures_pnl({})
    assert out == {
        "realized_pnl": 0.0,
        "realized_pnl_without_fees": 0.0,
        "total_fee": 0.0,
        "total_commission": 0.0,
        "total_gold_savings": 0.0,
    }


def test_extract_futures_pnl_none_order_returns_zeros() -> None:
    out = futures.extract_futures_pnl(None)
    assert out["realized_pnl"] == 0.0


def test_extract_futures_pnl_full_order() -> None:
    order = {
        "realizedPnl": {
            "realizedPnl": {"amount": "-50.00"},
            "realizedPnlWithoutFees": {"amount": "-46.90"},
        },
        "totalFee": {"amount": "3.10"},
        "totalCommission": {"amount": "2.48"},
        "totalGoldSavings": {"amount": "0.62"},
    }
    out = futures.extract_futures_pnl(order)
    assert out["realized_pnl"] == -50.0
    assert out["realized_pnl_without_fees"] == -46.9
    assert out["total_fee"] == 3.10
    assert out["total_commission"] == 2.48
    assert out["total_gold_savings"] == 0.62


def test_extract_futures_pnl_realized_pnl_not_dict_is_ignored() -> None:
    """If realizedPnl is a string (malformed), the nested branch is skipped."""
    out = futures.extract_futures_pnl({"realizedPnl": "garbage"})
    assert out["realized_pnl"] == 0.0


def test_extract_futures_pnl_falsy_realized_pnl_object() -> None:
    """``realizedPnl: None`` and ``realizedPnl: {}`` both skip the nested branch."""
    out = futures.extract_futures_pnl({"realizedPnl": None})
    assert out["realized_pnl"] == 0.0
    out = futures.extract_futures_pnl({"realizedPnl": {}})
    assert out["realized_pnl"] == 0.0


def test_extract_futures_pnl_partial_nested() -> None:
    """Only realizedPnl present (no realizedPnlWithoutFees)."""
    order = {"realizedPnl": {"realizedPnl": {"amount": "100"}}}
    out = futures.extract_futures_pnl(order)
    assert out["realized_pnl"] == 100.0
    assert out["realized_pnl_without_fees"] == 0.0


# ---------------------------------------------------------------------------
# calculate_total_futures_pnl — only counts CLOSING orders
# ---------------------------------------------------------------------------


def test_calculate_total_futures_pnl_only_counts_closing() -> None:
    orders = [
        {
            "positionEffectAtPlacementTime": "OPENING",
            "realizedPnl": {"realizedPnl": {"amount": "999"}},
            "totalFee": {"amount": "1"},
        },
        {
            "positionEffectAtPlacementTime": "CLOSING",
            "realizedPnl": {
                "realizedPnl": {"amount": "100"},
                "realizedPnlWithoutFees": {"amount": "103.10"},
            },
            "totalFee": {"amount": "3.10"},
            "totalCommission": {"amount": "2.48"},
            "totalGoldSavings": {"amount": "0.62"},
        },
        {
            "positionEffectAtPlacementTime": "CLOSING",
            "realizedPnl": {
                "realizedPnl": {"amount": "-50"},
                "realizedPnlWithoutFees": {"amount": "-46.90"},
            },
            "totalFee": {"amount": "3.10"},
            "totalCommission": {"amount": "2.48"},
            "totalGoldSavings": {"amount": "0.62"},
        },
    ]
    out = futures.calculate_total_futures_pnl(orders)
    assert out["num_orders"] == 2
    assert out["total_pnl"] == pytest.approx(50.0)
    assert out["total_pnl_without_fees"] == pytest.approx(56.20)
    assert out["total_fees"] == pytest.approx(6.20)
    assert out["total_commissions"] == pytest.approx(4.96)
    assert out["total_gold_savings"] == pytest.approx(1.24)


def test_calculate_total_futures_pnl_empty_list_returns_zeros() -> None:
    out = futures.calculate_total_futures_pnl([])
    assert out["num_orders"] == 0
    assert out["total_pnl"] == 0.0


def test_calculate_total_futures_pnl_none_returns_zeros() -> None:
    out = futures.calculate_total_futures_pnl(None)
    assert out["num_orders"] == 0


def test_calculate_total_futures_pnl_skips_orders_without_position_effect() -> None:
    """Orders missing positionEffectAtPlacementTime are not counted."""
    orders = [
        {
            "realizedPnl": {"realizedPnl": {"amount": "100"}},
            "totalFee": {"amount": "1"},
        }
    ]
    out = futures.calculate_total_futures_pnl(orders)
    assert out["num_orders"] == 0
    assert out["total_pnl"] == 0.0
