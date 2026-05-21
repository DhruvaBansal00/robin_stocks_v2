"""Robinhood CSV export tools (write to disk)."""

from __future__ import annotations

from typing import Optional

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool(write=True)
async def rh_export_completed_stock_orders(
    dir_path: str, file_name: Optional[str] = None, account_number: Optional[str] = None
) -> str:
    """Write all completed stock orders to a CSV in dir_path."""
    await to_thread(
        rh.export_completed_stock_orders, dir_path, file_name=file_name, account_number=account_number
    )
    return f"ok: stock orders exported to {dir_path}"


@mcp.tool()
@safe_tool(write=True)
async def rh_export_completed_crypto_orders(
    dir_path: str, file_name: Optional[str] = None
) -> str:
    """Write all completed crypto orders to a CSV in dir_path."""
    await to_thread(rh.export_completed_crypto_orders, dir_path, file_name=file_name)
    return f"ok: crypto orders exported to {dir_path}"


@mcp.tool()
@safe_tool(write=True)
async def rh_export_completed_option_orders(
    dir_path: str, file_name: Optional[str] = None
) -> str:
    """Write all completed option orders to a CSV in dir_path."""
    await to_thread(rh.export_completed_option_orders, dir_path, file_name=file_name)
    return f"ok: option orders exported to {dir_path}"
