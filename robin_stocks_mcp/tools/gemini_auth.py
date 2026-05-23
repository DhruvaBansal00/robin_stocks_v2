"""Gemini authentication tools."""

from __future__ import annotations

from typing import Any

import robin_stocks.gemini as gem

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def gem_login(api_key: str, secret_key: str) -> str:
    """Authenticate with Gemini using an API key + secret pair."""
    await to_thread(gem.login, api_key, secret_key)
    return "ok: Gemini login complete"


@mcp.tool()
@safe_tool()
async def gem_logout() -> str:
    """Remove the Gemini API/secret key from the session."""
    await to_thread(gem.logout)
    return "ok: logged out of Gemini"


@mcp.tool()
@safe_tool()
async def gem_heartbeat(jsonify: bool | None = None) -> Any:
    """Send a heartbeat to keep the Gemini session alive."""
    return await to_thread(gem.heartbeat, jsonify=jsonify)


@mcp.tool()
@safe_tool()
async def gem_use_sandbox(use_sandbox: bool) -> str:
    """Switch between the Gemini live and sandbox API base URLs."""
    await to_thread(gem.use_sand_box_urls, use_sandbox)
    return f"ok: Gemini sandbox={'on' if use_sandbox else 'off'}"
