"""Mocked unit tests for robin_stocks.robinhood.prediction_markets.

Covers browse (categories/events/contracts), account discovery, positions,
cursor-paginated orders, order info lookup, fee preview, order placement, and
cancellation. Fully offline — every network helper is patched.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import prediction_markets as pm

MOD = "robin_stocks.robinhood.prediction_markets"


@pytest.fixture(autouse=True)
def _logged_in():
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        yield


# ---------------------------------------------------------------------------
# Browse functions
# ---------------------------------------------------------------------------


def test_get_categories_returns_nodes() -> None:
    with (
        patch(f"{MOD}.request_get", return_value={"nodeId": "x", "nodes": [{"id": "1"}, {"id": "2"}]}),
        patch(f"{MOD}.update_session_for_futures") as upd,
    ):
        out = pm.get_prediction_market_categories()
    upd.assert_called_once()
    assert out == [{"id": "1"}, {"id": "2"}]


def test_get_categories_no_nodes_returns_none() -> None:
    with (
        patch(f"{MOD}.request_get", return_value={"detail": "nope"}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_prediction_market_categories() is None


def test_get_events_passes_category_payload() -> None:
    with (
        patch(f"{MOD}.request_get", return_value={"results": [{"id": "e1"}]}) as rg,
        patch(f"{MOD}.update_session_for_futures"),
    ):
        out = pm.get_prediction_market_events("Crypto")
    assert rg.call_args[1]["payload"] == {"categories": "Crypto"}
    assert out == [{"id": "e1"}]


def test_get_events_no_results_returns_none() -> None:
    with (
        patch(f"{MOD}.request_get", return_value=None),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_prediction_market_events("Crypto") is None


def test_get_event_unwraps_results_then_falls_back() -> None:
    with (
        patch(f"{MOD}.request_get", return_value={"results": {"id": "e1"}}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_prediction_market_event("e1") == {"id": "e1"}

    with (
        patch(f"{MOD}.request_get", return_value={"id": "e2", "name": "n"}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_prediction_market_event("e2", info="name") == "n"


def test_get_event_contract_unwraps_event_contract_key() -> None:
    with (
        patch(f"{MOD}.request_get", return_value={"eventContract": {"id": "c1", "symbol": "KX"}}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_event_contract("c1", info="symbol") == "KX"


def test_get_event_contract_falls_back_to_raw() -> None:
    with (
        patch(f"{MOD}.request_get", return_value={"id": "c1"}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_event_contract("c1") == {"id": "c1"}


def test_get_node_id_resolves_display_name() -> None:
    nodes = [{"id": "n1", "displayHeaderText": "Crypto"}, {"id": "n2", "displayHeaderText": "Pro basketball"}]
    with patch(f"{MOD}.get_prediction_market_categories", return_value=nodes):
        assert pm.get_prediction_market_node_id("Pro basketball") == "n2"
        assert pm.get_prediction_market_node_id("Nonexistent") is None


def test_get_prediction_markets_resolves_category_then_fetches_layout() -> None:
    layout = {"results": {"nodeId": "n2", "components": [{"eventComponent": {"eventId": "e1"}}]}}
    with (
        patch(f"{MOD}.get_prediction_market_node_id", return_value="n2") as gnid,
        patch(f"{MOD}.request_get", return_value=layout) as rg,
        patch(f"{MOD}.update_session_for_futures"),
    ):
        out = pm.get_prediction_markets("Pro basketball")
    gnid.assert_called_once_with("Pro basketball")
    assert rg.call_args[1]["payload"] == {"node_id": "n2"}
    assert out == [{"eventComponent": {"eventId": "e1"}}]


def test_get_prediction_markets_accepts_node_id_directly() -> None:
    layout = {"results": {"components": []}}
    with (
        patch(f"{MOD}.get_prediction_market_node_id") as gnid,
        patch(f"{MOD}.request_get", return_value=layout) as rg,
        patch(f"{MOD}.update_session_for_futures"),
    ):
        pm.get_prediction_markets("77991bb6-9ad5-46cc-8bcf-fa0c7844a406")
    gnid.assert_not_called()
    assert rg.call_args[1]["payload"] == {"node_id": "77991bb6-9ad5-46cc-8bcf-fa0c7844a406"}


def test_get_prediction_markets_unresolved_returns_none() -> None:
    with patch(f"{MOD}.get_prediction_market_node_id", return_value=None):
        assert pm.get_prediction_markets("Nope") is None


# ---------------------------------------------------------------------------
# Account discovery
# ---------------------------------------------------------------------------


def test_account_id_finds_swap_account() -> None:
    data = [
        {"accountType": "FUTURES", "id": "fut"},
        {"accountType": "SWAP", "id": "swap"},
    ]
    with (
        patch(f"{MOD}.request_get", return_value=data),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_event_contracts_account_id() == "swap"


def test_account_id_none_when_no_swap() -> None:
    with (
        patch(f"{MOD}.request_get", return_value=[{"accountType": "FUTURES", "id": "fut"}]),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_event_contracts_account_id() is None


def test_account_id_ignores_non_dict_entries() -> None:
    data = ["garbage", {"accountType": "SWAP", "id": "swap"}]
    with (
        patch(f"{MOD}.request_get", return_value=data),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_event_contracts_account_id() == "swap"


def test_account_id_none_when_empty() -> None:
    with (
        patch(f"{MOD}.request_get", return_value=[]),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_event_contracts_account_id() is None


# ---------------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------------


def test_positions_uses_explicit_account() -> None:
    with (
        patch(f"{MOD}.request_get", return_value=[{"id": "p1"}]) as rg,
        patch(f"{MOD}.update_session_for_futures"),
        patch(f"{MOD}.event_contract_positions_url", return_value="https://x/") as url,
    ):
        out = pm.get_event_contract_positions(account_id="acct-1")
    url.assert_called_once_with("acct-1")
    assert rg.call_args[1]["dataType"] == "results"
    assert out == [{"id": "p1"}]


def test_positions_auto_detects_account() -> None:
    with (
        patch(f"{MOD}.get_event_contracts_account_id", return_value="auto") as gai,
        patch(f"{MOD}.request_get", return_value=[]),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        pm.get_event_contract_positions()
    gai.assert_called_once()


def test_positions_none_when_no_account() -> None:
    with patch(f"{MOD}.get_event_contracts_account_id", return_value=None):
        assert pm.get_event_contract_positions() is None


# ---------------------------------------------------------------------------
# Orders — cursor pagination
# ---------------------------------------------------------------------------


def test_orders_paginate_until_cursor_none() -> None:
    page1 = {"results": [{"id": "1"}], "next": "cur-2"}
    page2 = {"results": [{"id": "2"}], "next": None}
    with (
        patch(f"{MOD}.request_get", side_effect=[page1, page2]) as rg,
        patch(f"{MOD}.update_session_for_futures"),
    ):
        out = pm.get_event_contract_orders(account_id="acct-1")
    assert [o["id"] for o in out] == ["1", "2"]
    payloads = [c.kwargs["payload"] for c in rg.call_args_list]
    assert payloads[0] is None
    assert payloads[1] == {"cursor": "cur-2"}


def test_orders_terminate_on_missing_results() -> None:
    with (
        patch(f"{MOD}.request_get", return_value={"detail": "x"}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        assert pm.get_event_contract_orders(account_id="acct-1") == []


def test_orders_auto_detect_and_no_account() -> None:
    with (
        patch(f"{MOD}.get_event_contracts_account_id", return_value="auto") as gai,
        patch(f"{MOD}.request_get", return_value={"results": [], "next": None}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        pm.get_event_contract_orders()
    gai.assert_called_once()

    with patch(f"{MOD}.get_event_contracts_account_id", return_value=None):
        assert pm.get_event_contract_orders() is None


def test_order_info_matches_by_id_or_order_id() -> None:
    orders = [{"orderId": "a"}, {"id": "b"}]
    with patch(f"{MOD}.get_event_contract_orders", return_value=orders):
        assert pm.get_event_contract_order_info("a", account_id="x") == {"orderId": "a"}
        assert pm.get_event_contract_order_info("b", account_id="x") == {"id": "b"}
        assert pm.get_event_contract_order_info("zzz", account_id="x") is None


def test_order_info_none_when_no_orders() -> None:
    with patch(f"{MOD}.get_event_contract_orders", return_value=None):
        assert pm.get_event_contract_order_info("a") is None


# ---------------------------------------------------------------------------
# Leg builder
# ---------------------------------------------------------------------------


def test_build_leg_shape_and_uppercases_side() -> None:
    assert pm._build_leg("c1", "buy") == {
        "contract_id": "c1",
        "order_side": "BUY",
        "ratio_quantity": 1,
        "contract_type": "EVENT_CONTRACT",
    }


# ---------------------------------------------------------------------------
# Fee preview
# ---------------------------------------------------------------------------


def test_fee_preview_builds_tentative_order_and_posts_json() -> None:
    with (
        patch(f"{MOD}.request_post", return_value={"totalFee": {"amount": "0.02"}}) as rp,
        patch(f"{MOD}.update_session_for_futures"),
    ):
        out = pm.get_event_contract_order_fees("c1", "BUY", 2, "0.45", account_id="acct-1")
    body = rp.call_args[1]["payload"]
    assert rp.call_args[1]["json"] is True
    assert body["account_id"] == "acct-1"
    assert body["tentative_futures_order"]["order_type"] == "LIMIT"
    assert body["tentative_futures_order"]["quantity"] == "2"
    assert body["tentative_futures_order"]["limit_price"] == "0.45"
    assert body["tentative_futures_order"]["legs"][0]["contract_id"] == "c1"
    assert out == {"totalFee": {"amount": "0.02"}}


def test_fee_preview_none_when_no_account() -> None:
    with patch(f"{MOD}.get_event_contracts_account_id", return_value=None):
        assert pm.get_event_contract_order_fees("c1", "BUY", 1, "0.05") is None


# ---------------------------------------------------------------------------
# Order placement
# ---------------------------------------------------------------------------


CM = {
    "bid": {"value": "0.44"},
    "ask": {"value": "0.45"},
    "marketable": False,
    "platform": "api",
    "timestamp": {"value": "2026-05-23T17:00:00Z"},
}


def test_order_builds_payload_and_generates_ref_id() -> None:
    with (
        patch(f"{MOD}.request_post", return_value={"id": "order-1"}) as rp,
        patch(f"{MOD}.update_session_for_futures"),
    ):
        out = pm.order_event_contract("c1", "buy", 3, "0.40", CM, "q-1", account_id="acct-1")
    body = rp.call_args[1]["payload"]
    assert rp.call_args[1]["json"] is True
    assert body["account_id"] == "acct-1"
    assert body["quantity"] == "3"
    assert body["limit_price"] == "0.40"
    assert body["time_in_force"] == "GTC"
    assert body["legs"][0]["order_side"] == "BUY"
    assert body["quote_id"] == "q-1"
    assert body["client_marketdata"] == CM
    assert isinstance(body["ref_id"], str) and len(body["ref_id"]) > 0
    assert out == {"id": "order-1"}


def test_order_uses_explicit_ref_id_and_tif() -> None:
    with (
        patch(f"{MOD}.request_post", return_value={"id": "o"}) as rp,
        patch(f"{MOD}.update_session_for_futures"),
    ):
        pm.order_event_contract("c1", "SELL", 1, "0.30", CM, "q-2", account_id="a", time_in_force="ioc", ref_id="fixed-ref")
    body = rp.call_args[1]["payload"]
    assert body["ref_id"] == "fixed-ref"
    assert body["time_in_force"] == "IOC"
    assert body["legs"][0]["order_side"] == "SELL"


def test_order_auto_detects_account() -> None:
    with (
        patch(f"{MOD}.get_event_contracts_account_id", return_value="auto") as gai,
        patch(f"{MOD}.request_post", return_value={"id": "o"}),
        patch(f"{MOD}.update_session_for_futures"),
    ):
        pm.order_event_contract("c1", "BUY", 1, "0.20", CM, "q-3")
    gai.assert_called_once()


def test_order_none_when_no_account() -> None:
    with patch(f"{MOD}.get_event_contracts_account_id", return_value=None):
        assert pm.order_event_contract("c1", "BUY", 1, "0.20", CM, "q-4") is None


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------


def test_cancel_posts_to_cancel_url() -> None:
    with (
        patch(f"{MOD}.request_post", return_value={"state": "cancelled"}) as rp,
        patch(f"{MOD}.update_session_for_futures"),
        patch(f"{MOD}.event_contract_cancel_url", return_value="https://x/cancel") as url,
    ):
        out = pm.cancel_event_contract_order("order-1")
    url.assert_called_once_with("order-1")
    assert rp.call_args[1]["json"] is True
    assert out == {"state": "cancelled"}
