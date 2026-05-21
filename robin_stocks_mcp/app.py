"""Shared FastMCP instance imported by every tool module.

Kept separate from `server.py` so tool modules can `from .app import mcp`
without triggering CLI / argparse setup at import time.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "robin-stocks",
    instructions=(
        "Tools for interacting with Robinhood (`rh_*`), TD Ameritrade (`tda_*`), and Gemini "
        "(`gem_*`) via the robin_stocks Python SDK. Read-only by default; set "
        "ROBIN_STOCKS_MCP_READ_ONLY=false to enable order placement and other write tools. "
        "Call `rh_login` / `tda_login` / `gem_login` first if credentials were not provided via "
        "environment variables at startup."
    ),
)
