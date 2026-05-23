"""Tests that Gemini tools dispatch correctly to the SDK."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks_mcp.app import mcp


def get_fn(name: str):
    return mcp._tool_manager.get_tool(name).fn


@pytest.mark.asyncio
async def test_gem_login_dispatches() -> None:
    with patch("robin_stocks.gemini.login") as m:
        out = await get_fn("gem_login")(api_key="k", secret_key="s")
        m.assert_called_once_with("k", "s")
        assert out == "ok: Gemini login complete"


@pytest.mark.asyncio
async def test_gem_get_pubticker_dispatches() -> None:
    with patch("robin_stocks.gemini.get_pubticker", return_value={"last": "1"}) as m:
        await get_fn("gem_get_pubticker")(ticker="btcusd")
        m.assert_called_once_with("btcusd", jsonify=None)


@pytest.mark.asyncio
async def test_gem_check_available_balances_dispatches() -> None:
    with patch("robin_stocks.gemini.check_available_balances", return_value=[]) as m:
        await get_fn("gem_check_available_balances")()
        m.assert_called_once_with(jsonify=None)


@pytest.mark.asyncio
async def test_gem_order_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.gemini.order") as m:
        out = await get_fn("gem_order")(symbol="btcusd", side="buy", quantity=1.0)
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_gem_order_dispatches_when_enabled(writes_enabled) -> None:
    with patch("robin_stocks.gemini.order", return_value={"order_id": "x"}) as m:
        out = await get_fn("gem_order")(symbol="btcusd", side="buy", quantity=1.0, price=50000.0)
        m.assert_called_once_with(
            "btcusd",
            "buy",
            1.0,
            price=50000.0,
            order_type="exchange limit",
            options=None,
            jsonify=None,
        )
        assert out == {"order_id": "x"}


@pytest.mark.asyncio
async def test_gem_order_market_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.gemini.order_market") as m:
        out = await get_fn("gem_order_market")(symbol="btcusd", side="buy", quantity=1.0)
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_gem_cancel_all_active_orders_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.gemini.cancel_all_active_orders") as m:
        out = await get_fn("gem_cancel_all_active_orders")()
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_gem_withdraw_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.gemini.withdraw_crypto_funds") as m:
        out = await get_fn("gem_withdraw_crypto_funds")(address="addr", amount=1.0, currency="btc")
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_gem_use_sandbox_dispatches() -> None:
    with patch("robin_stocks.gemini.use_sand_box_urls") as m:
        out = await get_fn("gem_use_sandbox")(use_sandbox=True)
        m.assert_called_once_with(True)
        assert out == "ok: Gemini sandbox=on"


@pytest.mark.asyncio
async def test_gem_heartbeat_dispatches() -> None:
    with patch("robin_stocks.gemini.heartbeat", return_value={"result": "ok"}) as m:
        await get_fn("gem_heartbeat")()
        m.assert_called_once_with(jsonify=None)
