"""Dispatch tests for the Robinhood futures MCP tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks_mcp.app import mcp


def get_fn(name: str):
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None, f"tool '{name}' not registered"
    return tool.fn


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_get_futures_contract_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_futures_contract", return_value={"id": "abc"}) as m:
        out = await get_fn("rh_get_futures_contract")(symbol="ESH26")
        m.assert_called_once_with("ESH26", info=None)
        assert out == {"id": "abc"}


@pytest.mark.asyncio
async def test_rh_get_futures_contracts_by_symbols_dispatches() -> None:
    with patch(
        "robin_stocks.robinhood.get_futures_contracts_by_symbols",
        return_value=[{"id": "a"}, {"id": "b"}],
    ) as m:
        out = await get_fn("rh_get_futures_contracts_by_symbols")(symbols=["ESH26", "NQH26"])
        m.assert_called_once_with(["ESH26", "NQH26"], info=None)
        assert len(out) == 2


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_get_futures_quote_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_futures_quote", return_value={"bid_price": "100"}) as m:
        await get_fn("rh_get_futures_quote")(symbol="ESH26")
        m.assert_called_once_with("ESH26", info=None)


@pytest.mark.asyncio
async def test_rh_get_futures_quotes_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_futures_quotes", return_value=[{}]) as m:
        await get_fn("rh_get_futures_quotes")(symbols=["ESH26", "NQH26"])
        m.assert_called_once_with(["ESH26", "NQH26"], info=None)


@pytest.mark.asyncio
async def test_rh_get_futures_quote_by_id_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_futures_quote_by_id", return_value={"x": 1}) as m:
        await get_fn("rh_get_futures_quote_by_id")(contract_id="cid")
        m.assert_called_once_with("cid", info=None)


# ---------------------------------------------------------------------------
# Account & orders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_get_futures_account_id_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_futures_account_id", return_value="acct") as m:
        out = await get_fn("rh_get_futures_account_id")()
        m.assert_called_once_with()
        assert out == "acct"


@pytest.mark.asyncio
async def test_rh_get_futures_positions_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_futures_positions", return_value=None) as m:
        await get_fn("rh_get_futures_positions")(account_id="acct-1")
        m.assert_called_once_with(account_id="acct-1", info=None)


@pytest.mark.asyncio
async def test_rh_get_all_futures_orders_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_all_futures_orders", return_value=[]) as m:
        await get_fn("rh_get_all_futures_orders")()
        m.assert_called_once_with(account_id=None, info=None)


@pytest.mark.asyncio
async def test_rh_get_filled_futures_orders_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_filled_futures_orders", return_value=[]) as m:
        await get_fn("rh_get_filled_futures_orders")(account_id="acct")
        m.assert_called_once_with(account_id="acct", info=None)


@pytest.mark.asyncio
async def test_rh_get_futures_order_info_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_futures_order_info", return_value={"orderId": "o"}) as m:
        await get_fn("rh_get_futures_order_info")(order_id="o", account_id="a")
        m.assert_called_once_with("o", account_id="a", info=None)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_extract_futures_pnl_dispatches_real_logic() -> None:
    """No mocking — the helper is pure Python so we can verify real values."""
    sample = {
        "realizedPnl": {
            "realizedPnl": {"amount": "-50.00"},
            "realizedPnlWithoutFees": {"amount": "-46.90"},
        },
        "totalFee": {"amount": "3.10"},
        "totalCommission": {"amount": "2.48"},
        "totalGoldSavings": {"amount": "0.62"},
    }
    out = await get_fn("rh_extract_futures_pnl")(order=sample)
    assert abs(out["realized_pnl"] - (-50.00)) < 1e-6
    assert abs(out["total_fee"] - 3.10) < 1e-6


@pytest.mark.asyncio
async def test_rh_calculate_total_futures_pnl_only_counts_closing() -> None:
    """Open orders are filtered out by positionEffectAtPlacementTime."""
    orders = [
        {
            "positionEffectAtPlacementTime": "OPENING",
            "realizedPnl": {"realizedPnl": {"amount": "999"}},
            "totalFee": {"amount": "0"},
        },
        {
            "positionEffectAtPlacementTime": "CLOSING",
            "realizedPnl": {"realizedPnl": {"amount": "100"}},
            "totalFee": {"amount": "1"},
        },
    ]
    out = await get_fn("rh_calculate_total_futures_pnl")(orders=orders)
    assert out["num_orders"] == 1
    assert abs(out["total_pnl"] - 100.0) < 1e-6
