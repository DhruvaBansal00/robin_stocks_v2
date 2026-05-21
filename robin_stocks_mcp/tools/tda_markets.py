"""TD Ameritrade market tools."""

from __future__ import annotations

from typing import Any, List, Optional, Union

import robin_stocks.tda as tda

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def tda_get_hours_for_markets(
    markets: Union[str, List[str]], date: str, jsonify: Optional[bool] = None
) -> Any:
    """Market hours for one or more markets on a given date (YYYY-MM-DD)."""
    return await to_thread(tda.get_hours_for_markets, markets, date, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_hours_for_market(
    market: str, date: str, jsonify: Optional[bool] = None
) -> Any:
    """Market hours for a single market on a given date."""
    return await to_thread(tda.get_hours_for_market, market, date, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def tda_get_movers(
    market: str, direction: str, change: str, jsonify: Optional[bool] = None
) -> Any:
    """Market movers. market: $DJI / $COMPX / $SPX.X. direction: up/down. change: percent/value."""
    return await to_thread(tda.get_movers, market, direction, change, jsonify=jsonify)
