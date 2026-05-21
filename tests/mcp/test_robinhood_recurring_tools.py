"""Dispatch + read-only-guard tests for the Robinhood recurring-investment MCP tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks_mcp.app import mcp


def get_fn(name: str):
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None, f"tool '{name}' not registered"
    return tool.fn


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_get_recurring_investments_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_recurring_investments", return_value=[]) as m:
        await get_fn("rh_get_recurring_investments")(asset_types=["equity"])
        m.assert_called_once_with(info=None, account_number=None, asset_types=["equity"], jsonify=True)


@pytest.mark.asyncio
async def test_rh_get_next_investment_date_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_next_investment_date", return_value={"next_investment_date": "2026-05-27"}) as m:
        out = await get_fn("rh_get_next_investment_date")(frequency="weekly", start_date="2026-05-20")
        m.assert_called_once_with(frequency="weekly", start_date="2026-05-20", jsonify=True)
        assert out == {"next_investment_date": "2026-05-27"}


# ---------------------------------------------------------------------------
# Writes — guarded by read-only mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_create_recurring_investment_blocked_when_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.create_recurring_investment") as m:
        out = await get_fn("rh_create_recurring_investment")(symbol="AAPL", amount=5.0)
        assert out["error"] is True
        assert out["type"] == "ReadOnlyError"
        m.assert_not_called()


@pytest.mark.asyncio
async def test_rh_create_recurring_investment_dispatches_when_writes_enabled(writes_enabled) -> None:
    with patch("robin_stocks.robinhood.create_recurring_investment", return_value={"id": "sched-1"}) as m:
        out = await get_fn("rh_create_recurring_investment")(symbol="AAPL", amount=5.0)
        m.assert_called_once_with(
            "AAPL", 5.0,
            frequency="weekly",
            start_date=None,
            account_number=None,
            source_of_funds="buying_power",
            jsonify=True,
        )
        assert out == {"id": "sched-1"}


@pytest.mark.asyncio
async def test_rh_update_recurring_investment_blocked_when_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.update_recurring_investment") as m:
        out = await get_fn("rh_update_recurring_investment")(schedule_id="s1", state="paused")
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_rh_update_recurring_investment_dispatches_when_writes_enabled(writes_enabled) -> None:
    with patch("robin_stocks.robinhood.update_recurring_investment", return_value={"state": "paused"}) as m:
        await get_fn("rh_update_recurring_investment")(schedule_id="s1", state="paused")
        m.assert_called_once_with(
            "s1",
            account_number=None,
            amount=None,
            frequency=None,
            state="paused",
            start_date=None,
            jsonify=True,
        )


@pytest.mark.asyncio
async def test_rh_cancel_recurring_investment_blocked_when_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.cancel_recurring_investment") as m:
        out = await get_fn("rh_cancel_recurring_investment")(schedule_id="s1")
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_rh_cancel_recurring_investment_dispatches_when_writes_enabled(writes_enabled) -> None:
    with patch("robin_stocks.robinhood.cancel_recurring_investment", return_value={"state": "deleted"}) as m:
        await get_fn("rh_cancel_recurring_investment")(schedule_id="s1")
        m.assert_called_once_with("s1", jsonify=True)
