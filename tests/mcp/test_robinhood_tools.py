"""Tests that Robinhood tools dispatch correctly to the SDK and honour the read-only guard."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks_mcp.app import mcp


def get_fn(name: str):
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None, f"tool '{name}' not registered"
    return tool.fn


# ---------------------------------------------------------------------------
# Read-tool dispatch: each one should call the underlying SDK function exactly once
# and pass its arguments through.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_get_quotes_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_quotes", return_value=[{"symbol": "AAPL"}]) as m:
        out = await get_fn("rh_get_quotes")(inputSymbols="AAPL")
        m.assert_called_once_with("AAPL", info=None)
        assert out == [{"symbol": "AAPL"}]


@pytest.mark.asyncio
async def test_rh_get_latest_price_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_latest_price", return_value=["100.00"]) as m:
        out = await get_fn("rh_get_latest_price")(inputSymbols=["AAPL", "MSFT"])
        m.assert_called_once_with(["AAPL", "MSFT"], priceType=None, includeExtendedHours=True)
        assert out == ["100.00"]


@pytest.mark.asyncio
async def test_rh_build_holdings_dispatches() -> None:
    with patch("robin_stocks.robinhood.build_holdings", return_value={"AAPL": {}}) as m:
        out = await get_fn("rh_build_holdings")(with_dividends=True)
        m.assert_called_once_with(with_dividends=True)
        assert out == {"AAPL": {}}


@pytest.mark.asyncio
async def test_rh_get_market_hours_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_market_hours", return_value={"opens_at": "9:30"}) as m:
        await get_fn("rh_get_market_hours")(market="XNYS", date="2026-05-19")
        m.assert_called_once_with("XNYS", "2026-05-19", info=None)


@pytest.mark.asyncio
async def test_rh_get_crypto_quote_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_crypto_quote", return_value={"high_price": "1"}) as m:
        await get_fn("rh_get_crypto_quote")(symbol="BTC")
        m.assert_called_once_with("BTC", info=None)


@pytest.mark.asyncio
async def test_rh_get_open_crypto_positions_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_open_crypto_positions", return_value=[{"currency": "BTC"}]) as m:
        out = await get_fn("rh_get_open_crypto_positions")()
        m.assert_called_once_with(info=None)
        assert out == [{"currency": "BTC"}]


@pytest.mark.asyncio
async def test_rh_get_index_quote_by_id_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_index_quote_by_id", return_value={"last_trade_price": "100"}) as m:
        out = await get_fn("rh_get_index_quote_by_id")(stock_id="abc")
        m.assert_called_once_with("abc", info=None)
        assert out == {"last_trade_price": "100"}


@pytest.mark.asyncio
async def test_rh_find_tradable_options_dispatches() -> None:
    with patch("robin_stocks.robinhood.find_tradable_options", return_value=[]) as m:
        await get_fn("rh_find_tradable_options")(symbol="AAPL", expirationDate="2026-06-19")
        m.assert_called_once_with(
            "AAPL", expirationDate="2026-06-19", strikePrice=None, optionType=None, info=None
        )


@pytest.mark.asyncio
async def test_rh_find_stock_orders_unpacks_filters() -> None:
    with patch("robin_stocks.robinhood.find_stock_orders", return_value=[]) as m:
        await get_fn("rh_find_stock_orders")(filters={"state": "filled", "side": "buy"})
        m.assert_called_once_with(state="filled", side="buy")


# ---------------------------------------------------------------------------
# Tax-lot tools: three read tools and one write tool
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_get_tax_lots_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_tax_lots", return_value=[{"open_lot_id": "L1"}]) as m:
        out = await get_fn("rh_get_tax_lots")(symbol="AAPL")
        m.assert_called_once_with("AAPL", account_number=None, info=None)
        assert out == [{"open_lot_id": "L1"}]


@pytest.mark.asyncio
async def test_rh_get_selected_tax_lots_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_selected_tax_lots", return_value=[]) as m:
        await get_fn("rh_get_selected_tax_lots")(order_id="ord-1", account_number="acct-9")
        m.assert_called_once_with("ord-1", account_number="acct-9", info=None)


@pytest.mark.asyncio
async def test_rh_get_closed_tax_lots_dispatches() -> None:
    with patch("robin_stocks.robinhood.get_closed_tax_lots", return_value=[]) as m:
        await get_fn("rh_get_closed_tax_lots")(order_id="ord-2", info="term")
        m.assert_called_once_with("ord-2", account_number=None, info="term")


@pytest.mark.asyncio
async def test_rh_order_sell_tax_lot_blocked_when_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.order_sell_tax_lot") as m:
        out = await get_fn("rh_order_sell_tax_lot")(
            symbol="AAPL", lots=[{"open_lot_id": "L1", "quantity": "1"}]
        )
        assert out["error"] is True
        assert out["type"] == "ReadOnlyError"
        m.assert_not_called()


@pytest.mark.asyncio
async def test_rh_order_sell_tax_lot_dispatches_when_writes_enabled(writes_enabled) -> None:
    lots = [{"open_lot_id": "L1", "quantity": "1"}, {"open_lot_id": "L2", "quantity": "2"}]
    with patch("robin_stocks.robinhood.order_sell_tax_lot", return_value={"id": "abc"}) as m:
        out = await get_fn("rh_order_sell_tax_lot")(symbol="AAPL", lots=lots)
        m.assert_called_once_with(
            "AAPL",
            lots,
            account_number=None,
            timeInForce="gfd",
            extendedHours=False,
            jsonify=True,
            market_hours="regular_hours",
        )
        assert out == {"id": "abc"}


# ---------------------------------------------------------------------------
# Write-tool dispatch + read-only enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_order_buy_market_blocked_when_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.order_buy_market") as m:
        out = await get_fn("rh_order_buy_market")(symbol="AAPL", quantity=1)
        assert out["error"] is True
        assert out["type"] == "ReadOnlyError"
        m.assert_not_called()


@pytest.mark.asyncio
async def test_rh_order_buy_market_dispatches_when_writes_enabled(writes_enabled) -> None:
    with patch("robin_stocks.robinhood.order_buy_market", return_value={"id": "abc"}) as m:
        out = await get_fn("rh_order_buy_market")(symbol="AAPL", quantity=1)
        m.assert_called_once_with(
            "AAPL",
            1,
            account_number=None,
            timeInForce="gtc",
            extendedHours=False,
            jsonify=True,
        )
        assert out == {"id": "abc"}


@pytest.mark.asyncio
async def test_rh_cancel_all_stock_orders_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.cancel_all_stock_orders") as m:
        out = await get_fn("rh_cancel_all_stock_orders")()
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_rh_order_buy_limit_dispatches(writes_enabled) -> None:
    with patch("robin_stocks.robinhood.order_buy_limit", return_value={"id": "x"}) as m:
        await get_fn("rh_order_buy_limit")(symbol="AAPL", quantity=1, limitPrice=100.0)
        m.assert_called_once()
        args, kwargs = m.call_args
        assert args == ("AAPL", 1, 100.0)


@pytest.mark.asyncio
async def test_rh_export_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.export_completed_stock_orders") as m:
        out = await get_fn("rh_export_completed_stock_orders")(dir_path="/tmp")
        assert out["error"] is True
        m.assert_not_called()


# ---------------------------------------------------------------------------
# Error pass-through: SDK exceptions become structured errors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_get_quotes_propagates_sdk_error_safely() -> None:
    with patch("robin_stocks.robinhood.get_quotes", side_effect=RuntimeError("boom")):
        out = await get_fn("rh_get_quotes")(inputSymbols="AAPL")
        assert out["error"] is True
        assert out["type"] == "RuntimeError"
        assert "boom" in out["message"]


# ---------------------------------------------------------------------------
# Auth tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_login_passes_through_args() -> None:
    with patch("robin_stocks.robinhood.login", return_value={"access_token": "t"}) as m:
        out = await get_fn("rh_login")(username="u", password="p", mfa_code="123456")
        m.assert_called_once()
        _, kwargs = m.call_args
        assert kwargs["username"] == "u"
        assert kwargs["password"] == "p"
        assert kwargs["mfa_code"] == "123456"
        assert out == {"access_token": "t"}


@pytest.mark.asyncio
async def test_rh_logout_calls_logout() -> None:
    with patch("robin_stocks.robinhood.logout") as m:
        out = await get_fn("rh_logout")()
        m.assert_called_once_with()
        assert out == "ok: logged out of Robinhood"
