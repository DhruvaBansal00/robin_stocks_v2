"""Robinhood profile tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def rh_load_account_profile(
    account_number: str | None = None,
    info: str | None = None,
    dataType: str = "indexzero",
) -> Any:
    """Account profile: day-trading info, cash held by Robinhood, settled funds."""
    return await to_thread(rh.load_account_profile, account_number=account_number, info=info, dataType=dataType)


@mcp.tool()
@safe_tool()
async def rh_load_basic_profile(info: str | None = None) -> Any:
    """Personal profile: phone, city, marital status, date of birth."""
    return await to_thread(rh.load_basic_profile, info=info)


@mcp.tool()
@safe_tool()
async def rh_load_investment_profile(info: str | None = None) -> Any:
    """Investment profile from the new-account questionnaire."""
    return await to_thread(rh.load_investment_profile, info=info)


@mcp.tool()
@safe_tool()
async def rh_load_portfolio_profile(account_number: str | None = None, info: str | None = None) -> Any:
    """Portfolio profile: withdrawable amount, market value, excess margin."""
    return await to_thread(rh.load_portfolio_profile, account_number=account_number, info=info)


@mcp.tool()
@safe_tool()
async def rh_load_security_profile(info: str | None = None) -> Any:
    """Security profile."""
    return await to_thread(rh.load_security_profile, info=info)


@mcp.tool()
@safe_tool()
async def rh_load_user_profile(info: str | None = None) -> Any:
    """User profile: username, email, links to other profiles."""
    return await to_thread(rh.load_user_profile, info=info)
