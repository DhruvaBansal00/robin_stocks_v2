"""Robinhood order tools. Read tools are safe; placement/cancel are write-guarded."""

from __future__ import annotations

from typing import Any, Optional

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread

# ---------------------------------------------------------------------------
# Read tools (history / info / find)
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool()
async def rh_get_all_stock_orders(
    info: Optional[str] = None,
    account_number: Optional[str] = None,
    start_date: Optional[str] = None,
) -> Any:
    """All stock orders ever processed for the account."""
    return await to_thread(
        rh.get_all_stock_orders, info=info, account_number=account_number, start_date=start_date
    )


@mcp.tool()
@safe_tool()
async def rh_get_all_option_orders(
    info: Optional[str] = None,
    account_number: Optional[str] = None,
    start_date: Optional[str] = None,
) -> Any:
    """All option orders ever processed for the account."""
    return await to_thread(
        rh.get_all_option_orders, info=info, account_number=account_number, start_date=start_date
    )


@mcp.tool()
@safe_tool()
async def rh_get_all_crypto_orders(info: Optional[str] = None) -> Any:
    """All crypto orders ever processed for the account."""
    return await to_thread(rh.get_all_crypto_orders, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_all_open_stock_orders(
    info: Optional[str] = None, account_number: Optional[str] = None
) -> Any:
    """All currently-open stock orders."""
    return await to_thread(rh.get_all_open_stock_orders, info=info, account_number=account_number)


@mcp.tool()
@safe_tool()
async def rh_get_all_open_option_orders(
    info: Optional[str] = None, account_number: Optional[str] = None
) -> Any:
    """All currently-open option orders."""
    return await to_thread(rh.get_all_open_option_orders, info=info, account_number=account_number)


@mcp.tool()
@safe_tool()
async def rh_get_all_open_crypto_orders(info: Optional[str] = None) -> Any:
    """All currently-open crypto orders."""
    return await to_thread(rh.get_all_open_crypto_orders, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_stock_order_info(orderID: str) -> Any:
    """Info for a single stock order."""
    return await to_thread(rh.get_stock_order_info, orderID)


@mcp.tool()
@safe_tool()
async def rh_get_option_order_info(order_id: str) -> Any:
    """Info for a single option order."""
    return await to_thread(rh.get_option_order_info, order_id)


@mcp.tool()
@safe_tool()
async def rh_get_crypto_order_info(order_id: str) -> Any:
    """Info for a single crypto order."""
    return await to_thread(rh.get_crypto_order_info, order_id)


@mcp.tool()
@safe_tool()
async def rh_find_stock_orders(filters: dict) -> Any:
    """Find stock orders matching keyword filters (e.g. {'state': 'filled', 'side': 'buy'})."""
    return await to_thread(rh.find_stock_orders, **filters)


# ---------------------------------------------------------------------------
# Cancellation tools (write)
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_stock_order(orderID: str) -> Any:
    """Cancel a specific stock order."""
    return await to_thread(rh.cancel_stock_order, orderID)


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_option_order(orderID: str) -> Any:
    """Cancel a specific option order."""
    return await to_thread(rh.cancel_option_order, orderID)


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_crypto_order(orderID: str) -> Any:
    """Cancel a specific crypto order."""
    return await to_thread(rh.cancel_crypto_order, orderID)


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_all_stock_orders(account_number: Optional[str] = None) -> Any:
    """Cancel ALL open stock orders."""
    return await to_thread(rh.cancel_all_stock_orders, account_number=account_number)


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_all_option_orders(account_number: Optional[str] = None) -> Any:
    """Cancel ALL open option orders."""
    return await to_thread(rh.cancel_all_option_orders, account_number=account_number)


@mcp.tool()
@safe_tool(write=True)
async def rh_cancel_all_crypto_orders() -> Any:
    """Cancel ALL open crypto orders."""
    return await to_thread(rh.cancel_all_crypto_orders)


# ---------------------------------------------------------------------------
# Stock placement
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_market(
    symbol: str,
    quantity: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a market BUY order for whole shares."""
    return await to_thread(
        rh.order_buy_market,
        symbol,
        quantity,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_fractional_by_quantity(
    symbol: str,
    quantity: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gfd",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Buy fractional shares by quantity."""
    return await to_thread(
        rh.order_buy_fractional_by_quantity,
        symbol,
        quantity,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_fractional_by_price(
    symbol: str,
    amountInDollars: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gfd",
    extendedHours: bool = False,
    jsonify: bool = True,
    market_hours: str = "regular_hours",
) -> Any:
    """Buy fractional shares by dollar amount."""
    return await to_thread(
        rh.order_buy_fractional_by_price,
        symbol,
        amountInDollars,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
        market_hours=market_hours,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_limit(
    symbol: str,
    quantity: float,
    limitPrice: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a limit BUY order."""
    return await to_thread(
        rh.order_buy_limit,
        symbol,
        quantity,
        limitPrice,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_stop_loss(
    symbol: str,
    quantity: float,
    stopPrice: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a stop-loss BUY order (turns into a market order at stopPrice)."""
    return await to_thread(
        rh.order_buy_stop_loss,
        symbol,
        quantity,
        stopPrice,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_stop_limit(
    symbol: str,
    quantity: float,
    limitPrice: float,
    stopPrice: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a stop-limit BUY order."""
    return await to_thread(
        rh.order_buy_stop_limit,
        symbol,
        quantity,
        limitPrice,
        stopPrice,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_trailing_stop(
    symbol: str,
    quantity: float,
    trailAmount: float,
    trailType: str = "percentage",
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a trailing-stop BUY order."""
    return await to_thread(
        rh.order_buy_trailing_stop,
        symbol,
        quantity,
        trailAmount,
        trailType=trailType,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_market(
    symbol: str,
    quantity: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a market SELL order for whole shares."""
    return await to_thread(
        rh.order_sell_market,
        symbol,
        quantity,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_tax_lot(
    symbol: str,
    lots: list[dict],
    account_number: Optional[str] = None,
    timeInForce: str = "gfd",
    extendedHours: bool = False,
    jsonify: bool = True,
    market_hours: str = "regular_hours",
) -> Any:
    """Market SELL that closes specific open tax lots (the "Sell by Lot" flow).

    `lots` is a list of dicts each with keys 'open_lot_id' and 'quantity'.
    Lot ids come from rh_get_tax_lots(symbol).
    """
    return await to_thread(
        rh.order_sell_tax_lot,
        symbol,
        lots,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
        market_hours=market_hours,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_fractional_by_quantity(
    symbol: str,
    quantity: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gfd",
    priceType: str = "bid_price",
    extendedHours: bool = False,
    jsonify: bool = True,
    market_hours: str = "regular_hours",
) -> Any:
    """Sell fractional shares by quantity."""
    return await to_thread(
        rh.order_sell_fractional_by_quantity,
        symbol,
        quantity,
        account_number=account_number,
        timeInForce=timeInForce,
        priceType=priceType,
        extendedHours=extendedHours,
        jsonify=jsonify,
        market_hours=market_hours,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_fractional_by_price(
    symbol: str,
    amountInDollars: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gfd",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Sell fractional shares by dollar amount."""
    return await to_thread(
        rh.order_sell_fractional_by_price,
        symbol,
        amountInDollars,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_limit(
    symbol: str,
    quantity: float,
    limitPrice: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a limit SELL order."""
    return await to_thread(
        rh.order_sell_limit,
        symbol,
        quantity,
        limitPrice,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_stop_loss(
    symbol: str,
    quantity: float,
    stopPrice: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a stop-loss SELL order."""
    return await to_thread(
        rh.order_sell_stop_loss,
        symbol,
        quantity,
        stopPrice,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_stop_limit(
    symbol: str,
    quantity: float,
    limitPrice: float,
    stopPrice: float,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a stop-limit SELL order."""
    return await to_thread(
        rh.order_sell_stop_limit,
        symbol,
        quantity,
        limitPrice,
        stopPrice,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_trailing_stop(
    symbol: str,
    quantity: float,
    trailAmount: float,
    trailType: str = "percentage",
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
) -> Any:
    """Place a trailing-stop SELL order."""
    return await to_thread(
        rh.order_sell_trailing_stop,
        symbol,
        quantity,
        trailAmount,
        trailType=trailType,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order(
    symbol: str,
    quantity: float,
    side: str,
    limitPrice: Optional[float] = None,
    stopPrice: Optional[float] = None,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    extendedHours: bool = False,
    jsonify: bool = True,
    market_hours: str = "regular_hours",
) -> Any:
    """Generic stock order. side: 'buy'/'sell'. Provide limitPrice/stopPrice to vary order type."""
    return await to_thread(
        rh.order,
        symbol,
        quantity,
        side,
        limitPrice=limitPrice,
        stopPrice=stopPrice,
        account_number=account_number,
        timeInForce=timeInForce,
        extendedHours=extendedHours,
        jsonify=jsonify,
        market_hours=market_hours,
    )


# ---------------------------------------------------------------------------
# Option placement
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool(write=True)
async def rh_order_option_credit_spread(
    price: float,
    symbol: str,
    quantity: int,
    spread: list,
    timeInForce: str = "gtc",
    account_number: Optional[str] = None,
    jsonify: bool = True,
) -> Any:
    """Place an option credit spread order. `spread` is a list of leg dicts."""
    return await to_thread(
        rh.order_option_credit_spread,
        price,
        symbol,
        quantity,
        spread,
        timeInForce=timeInForce,
        account_number=account_number,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_option_debit_spread(
    price: float,
    symbol: str,
    quantity: int,
    spread: list,
    timeInForce: str = "gtc",
    account_number: Optional[str] = None,
    jsonify: bool = True,
) -> Any:
    """Place an option debit spread order."""
    return await to_thread(
        rh.order_option_debit_spread,
        price,
        symbol,
        quantity,
        spread,
        timeInForce=timeInForce,
        account_number=account_number,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_option_spread(
    direction: str,
    price: float,
    symbol: str,
    quantity: int,
    spread: list,
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Place a generic option spread order. direction: 'credit'/'debit'."""
    return await to_thread(
        rh.order_option_spread,
        direction,
        price,
        symbol,
        quantity,
        spread,
        account_number=account_number,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_option_limit(
    positionEffect: str,
    creditOrDebit: str,
    price: float,
    symbol: str,
    quantity: int,
    expirationDate: str,
    strike: float,
    optionType: str = "both",
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Limit BUY for an option. positionEffect: 'open'/'close'."""
    return await to_thread(
        rh.order_buy_option_limit,
        positionEffect,
        creditOrDebit,
        price,
        symbol,
        quantity,
        expirationDate,
        strike,
        optionType=optionType,
        account_number=account_number,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_option_stop_limit(
    positionEffect: str,
    creditOrDebit: str,
    limitPrice: float,
    stopPrice: float,
    symbol: str,
    quantity: int,
    expirationDate: str,
    strike: float,
    optionType: str = "both",
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Stop-limit BUY for an option."""
    return await to_thread(
        rh.order_buy_option_stop_limit,
        positionEffect,
        creditOrDebit,
        limitPrice,
        stopPrice,
        symbol,
        quantity,
        expirationDate,
        strike,
        optionType=optionType,
        account_number=account_number,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_option_stop_limit(
    positionEffect: str,
    creditOrDebit: str,
    limitPrice: float,
    stopPrice: float,
    symbol: str,
    quantity: int,
    expirationDate: str,
    strike: float,
    optionType: str = "both",
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Stop-limit SELL for an option."""
    return await to_thread(
        rh.order_sell_option_stop_limit,
        positionEffect,
        creditOrDebit,
        limitPrice,
        stopPrice,
        symbol,
        quantity,
        expirationDate,
        strike,
        optionType=optionType,
        account_number=account_number,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_option_limit(
    positionEffect: str,
    creditOrDebit: str,
    price: float,
    symbol: str,
    quantity: int,
    expirationDate: str,
    strike: float,
    optionType: str = "both",
    account_number: Optional[str] = None,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Limit SELL for an option."""
    return await to_thread(
        rh.order_sell_option_limit,
        positionEffect,
        creditOrDebit,
        price,
        symbol,
        quantity,
        expirationDate,
        strike,
        optionType=optionType,
        account_number=account_number,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )


# ---------------------------------------------------------------------------
# Crypto placement
# ---------------------------------------------------------------------------


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_crypto_by_price(
    symbol: str, amountInDollars: float, timeInForce: str = "gtc", jsonify: bool = True
) -> Any:
    """Market BUY crypto by dollar amount."""
    return await to_thread(
        rh.order_buy_crypto_by_price, symbol, amountInDollars, timeInForce=timeInForce, jsonify=jsonify
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_crypto_by_quantity(
    symbol: str, quantity: float, timeInForce: str = "gtc", jsonify: bool = True
) -> Any:
    """Market BUY crypto by quantity."""
    return await to_thread(
        rh.order_buy_crypto_by_quantity, symbol, quantity, timeInForce=timeInForce, jsonify=jsonify
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_crypto_limit(
    symbol: str, quantity: float, limitPrice: float, timeInForce: str = "gtc", jsonify: bool = True
) -> Any:
    """Limit BUY crypto by quantity."""
    return await to_thread(
        rh.order_buy_crypto_limit, symbol, quantity, limitPrice, timeInForce=timeInForce, jsonify=jsonify
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_buy_crypto_limit_by_price(
    symbol: str,
    amountInDollars: float,
    limitPrice: float,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Limit BUY crypto by dollar amount."""
    return await to_thread(
        rh.order_buy_crypto_limit_by_price,
        symbol,
        amountInDollars,
        limitPrice,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_crypto_by_price(
    symbol: str, amountInDollars: float, timeInForce: str = "gtc", jsonify: bool = True
) -> Any:
    """Market SELL crypto by dollar amount."""
    return await to_thread(
        rh.order_sell_crypto_by_price, symbol, amountInDollars, timeInForce=timeInForce, jsonify=jsonify
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_crypto_by_quantity(
    symbol: str, quantity: float, timeInForce: str = "gtc", jsonify: bool = True
) -> Any:
    """Market SELL crypto by quantity."""
    return await to_thread(
        rh.order_sell_crypto_by_quantity, symbol, quantity, timeInForce=timeInForce, jsonify=jsonify
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_crypto_limit(
    symbol: str, quantity: float, limitPrice: float, timeInForce: str = "gtc", jsonify: bool = True
) -> Any:
    """Limit SELL crypto by quantity."""
    return await to_thread(
        rh.order_sell_crypto_limit, symbol, quantity, limitPrice, timeInForce=timeInForce, jsonify=jsonify
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_sell_crypto_limit_by_price(
    symbol: str,
    amountInDollars: float,
    limitPrice: float,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Limit SELL crypto by dollar amount."""
    return await to_thread(
        rh.order_sell_crypto_limit_by_price,
        symbol,
        amountInDollars,
        limitPrice,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool(write=True)
async def rh_order_crypto(
    symbol: str,
    side: str,
    quantityOrPrice: float,
    amountIn: str = "quantity",
    limitPrice: Optional[float] = None,
    timeInForce: str = "gtc",
    jsonify: bool = True,
) -> Any:
    """Generic crypto order. side: 'buy'/'sell'. amountIn: 'quantity'/'dollars'."""
    return await to_thread(
        rh.order_crypto,
        symbol,
        side,
        quantityOrPrice,
        amountIn=amountIn,
        limitPrice=limitPrice,
        timeInForce=timeInForce,
        jsonify=jsonify,
    )
