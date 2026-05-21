"""Tests that TDA tools dispatch correctly to the SDK and enforce the write guard."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks_mcp.app import mcp


def get_fn(name: str):
    return mcp._tool_manager.get_tool(name).fn


@pytest.mark.asyncio
async def test_tda_login_dispatches() -> None:
    with patch("robin_stocks.tda.login") as m:
        out = await get_fn("tda_login")(encryption_passcode="pp")
        m.assert_called_once_with("pp")
        assert out == "ok: TDA login complete"


@pytest.mark.asyncio
async def test_tda_get_accounts_dispatches() -> None:
    with patch("robin_stocks.tda.get_accounts", return_value=[{"id": "1"}]) as m:
        out = await get_fn("tda_get_accounts")(options="positions")
        m.assert_called_once_with(options="positions", jsonify=None)
        assert out == [{"id": "1"}]


@pytest.mark.asyncio
async def test_tda_get_quote_dispatches() -> None:
    with patch("robin_stocks.tda.get_quote", return_value={"AAPL": {}}) as m:
        await get_fn("tda_get_quote")(ticker="AAPL")
        m.assert_called_once_with("AAPL", jsonify=None)


@pytest.mark.asyncio
async def test_tda_get_price_history_dispatches() -> None:
    with patch("robin_stocks.tda.get_price_history", return_value={"candles": []}) as m:
        await get_fn("tda_get_price_history")(
            ticker="AAPL",
            period_type="day",
            frequency_type="minute",
            frequency="5",
        )
        args, _ = m.call_args
        assert args[0:4] == ("AAPL", "day", "minute", "5")


@pytest.mark.asyncio
async def test_tda_place_order_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.tda.place_order") as m:
        out = await get_fn("tda_place_order")(account_id="1", order_payload={"x": 1})
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_tda_place_order_dispatches_when_enabled(writes_enabled) -> None:
    with patch("robin_stocks.tda.place_order", return_value={"orderId": "abc"}) as m:
        out = await get_fn("tda_place_order")(account_id="1", order_payload={"x": 1})
        m.assert_called_once_with("1", {"x": 1}, jsonify=None)
        assert out == {"orderId": "abc"}


@pytest.mark.asyncio
async def test_tda_cancel_order_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.tda.cancel_order") as m:
        out = await get_fn("tda_cancel_order")(account_id="1", order_id="x")
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_tda_get_option_chains_passes_kwargs() -> None:
    with patch("robin_stocks.tda.get_option_chains", return_value={}) as m:
        await get_fn("tda_get_option_chains")(ticker="AAPL", strike_count="5")
        _, kwargs = m.call_args
        assert kwargs["strike_count"] == "5"


@pytest.mark.asyncio
async def test_tda_get_movers_dispatches() -> None:
    with patch("robin_stocks.tda.get_movers", return_value=[]) as m:
        await get_fn("tda_get_movers")(market="$DJI", direction="up", change="percent")
        m.assert_called_once_with("$DJI", "up", "percent", jsonify=None)
