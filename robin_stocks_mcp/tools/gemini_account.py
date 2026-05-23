"""Gemini account tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.gemini as gem

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def gem_get_account_detail(jsonify: bool | None = None) -> Any:
    """Information about the profile attached to the Gemini API key."""
    return await to_thread(gem.get_account_detail, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_check_available_balances(jsonify: bool | None = None) -> Any:
    """Available balances per currency."""
    return await to_thread(gem.check_available_balances, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_check_notional_balances(jsonify: bool | None = None) -> Any:
    """Notional (USD) balances per currency."""
    return await to_thread(gem.check_notional_balances, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_check_transfers(
    timestamp: str | None = None,
    limit_transfers: int = 10,
    show_completed_deposit_advances: bool = False,
    jsonify: bool | None = None,
) -> Any:
    """List transfer history on Gemini."""
    return await to_thread(
        gem.check_transfers,
        timestamp=timestamp,
        limit_transfers=limit_transfers,
        show_completed_deposit_advances=show_completed_deposit_advances,
        jsonify=jsonify,
    )


@mcp.tool()
@safe_tool()
async def gem_get_deposit_addresses(network: str, timestamp: str | None = None, jsonify: bool | None = None) -> Any:
    """Get deposit addresses for a given network (e.g. 'bitcoin', 'ethereum')."""
    return await to_thread(gem.get_deposit_addresses, network, timestamp=timestamp, jsonify=jsonify)


@mcp.tool()
@safe_tool(write=True)
async def gem_withdraw_crypto_funds(address: str, amount: float, currency: str, jsonify: bool | None = None) -> Any:
    """Withdraw crypto from Gemini to a destination address."""
    return await to_thread(gem.withdraw_crypto_funds, address, amount, currency, jsonify=jsonify)
