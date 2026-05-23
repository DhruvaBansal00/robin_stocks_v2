"""Shared test fixtures for the robin_stocks_mcp test suite."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import pytest

from robin_stocks_mcp import runtime
from robin_stocks_mcp.app import mcp as mcp_app
from robin_stocks_mcp.config import Config


def _import_all_tool_modules() -> None:
    """Force-import every tool module so the FastMCP instance is fully populated."""
    from robin_stocks_mcp.tools import (  # noqa: F401
        gemini_account,
        gemini_auth,
        gemini_crypto,
        gemini_orders,
        robinhood_account,
        robinhood_auth,
        robinhood_crypto,
        robinhood_export,
        robinhood_futures,
        robinhood_markets,
        robinhood_options,
        robinhood_orders,
        robinhood_profiles,
        robinhood_recurring,
        robinhood_stocks,
        tda_account,
        tda_auth,
        tda_markets,
        tda_orders,
        tda_stocks,
    )


@pytest.fixture(scope="session", autouse=True)
def _register_tools() -> None:
    """Import every tool module exactly once for the test session.

    Tool modules that can't be imported (because they don't exist yet) are skipped silently
    so partial test runs work during incremental development.
    """
    try:
        _import_all_tool_modules()
    except ImportError:
        pass


@pytest.fixture
def writes_enabled() -> Any:
    """Temporarily disable the read-only guard for write-tool tests."""
    original = runtime.get_config()
    runtime.set_config(Config(**{**original.__dict__, "read_only": False}))
    yield
    runtime.set_config(original)


@pytest.fixture
def writes_disabled() -> Any:
    """Force the read-only guard on."""
    original = runtime.get_config()
    runtime.set_config(Config(**{**original.__dict__, "read_only": True}))
    yield
    runtime.set_config(original)


def get_tool_fn(name: str) -> Callable[..., Any]:
    """Look up a registered FastMCP tool's underlying async function by name."""
    tool = mcp_app._tool_manager.get_tool(name)
    if tool is None:
        raise KeyError(f"tool '{name}' is not registered")
    return tool.fn


def call_tool(name: str, **kwargs: Any) -> Any:
    """Synchronously invoke a registered tool (waits for the coroutine to finish)."""
    fn = get_tool_fn(name)
    coro = fn(**kwargs)
    if asyncio.iscoroutine(coro):
        return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)
    return coro


@pytest.fixture
def call() -> Callable[..., Any]:
    return call_tool


@pytest.fixture
def get_fn() -> Callable[..., Callable[..., Any]]:
    return get_tool_fn
