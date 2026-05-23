"""Generic dispatch coverage for every registered MCP tool.

Rather than hand-writing a test per tool, this introspects each registered
tool, derives the SDK function it should call (by stripping the broker
prefix), patches that function, synthesizes arguments from the tool's
signature, and asserts the call is forwarded.

Write tools are exercised with the read-only guard disabled.
"""

from __future__ import annotations

import inspect
from typing import Any, get_args, get_origin
from unittest.mock import patch

import pytest

import robin_stocks.gemini as gem
import robin_stocks.robinhood as rh
import robin_stocks.tda as tda
from robin_stocks_mcp import runtime
from robin_stocks_mcp.app import mcp
from robin_stocks_mcp.config import Config


def _force_register_tools() -> None:
    """Import every tool module so the FastMCP registry is populated at
    collection time (the session autouse fixture runs too late for this)."""
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


_force_register_tools()

PREFIX_TO_MODULE = {"rh_": rh, "tda_": tda, "gem_": gem}

# Tools that don't map 1:1 to a single SDK function, or have side effects we
# don't want to invoke generically. They are covered by dedicated tests.
SKIP_TOOLS = {
    # auth/login tools have bespoke argument handling + dedicated tests
    "rh_login",
    "rh_logout",
    "tda_login",
    "tda_login_first_time",
    "gem_login",
    # download tools write to disk with bespoke return strings
    "rh_download_document",
    "rh_download_all_documents",
    # unpacks **filters (empty dict ⇒ no-arg call); covered by a dedicated test
    "rh_find_stock_orders",
}


def _module_for(name: str):
    for prefix, module in PREFIX_TO_MODULE.items():
        if name.startswith(prefix):
            return prefix, module
    return None, None


def _sdk_attr(name: str) -> str:
    """rh_get_quotes -> get_quotes; tda_get_quote -> get_quote."""
    for prefix in PREFIX_TO_MODULE:
        if name.startswith(prefix):
            return name[len(prefix) :]
    return name


def _dummy_for_param(param: inspect.Parameter) -> Any:
    """Synthesize a plausible value for a required parameter based on its annotation."""
    ann = param.annotation
    origin = get_origin(ann)
    # Optional[X] / Union types
    if origin is not None:
        args = [a for a in get_args(ann) if a is not type(None)]
        ann = args[0] if args else str
        origin = get_origin(ann)
    if ann in (int,):
        return 1
    if ann in (float,):
        return 1.0
    if ann in (bool,):
        return True
    if origin in (list,) or ann in (list,):
        return []
    if origin in (dict,) or ann in (dict,):
        return {}
    return "X"  # default to a string


def _build_kwargs(fn) -> dict:
    """Build kwargs covering every required (no-default) parameter."""
    sig = inspect.signature(fn)
    kwargs = {}
    for pname, param in sig.parameters.items():
        if param.default is inspect.Parameter.empty and param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            kwargs[pname] = _dummy_for_param(param)
    return kwargs


def _all_dispatchable_tools():
    out = []
    for tool in mcp._tool_manager.list_tools():
        name = tool.name
        if name in SKIP_TOOLS:
            continue
        prefix, module = _module_for(name)
        if module is None:
            continue
        attr = _sdk_attr(name)
        if not hasattr(module, attr):
            continue  # tool name doesn't map to a single SDK function
        out.append((name, module, attr, tool.fn))
    return out


DISPATCHABLE = _all_dispatchable_tools()


@pytest.fixture
def _writes_enabled():
    original = runtime.get_config()
    runtime.set_config(Config(**{**original.__dict__, "read_only": False}))
    yield
    runtime.set_config(original)


def test_dispatch_table_is_substantial() -> None:
    """Sanity check: the introspection should find a large set of tools."""
    assert len(DISPATCHABLE) >= 120, f"only found {len(DISPATCHABLE)} dispatchable tools"


@pytest.mark.asyncio
@pytest.mark.parametrize("name,module,attr,fn", DISPATCHABLE, ids=[d[0] for d in DISPATCHABLE])
async def test_tool_forwards_to_sdk(name, module, attr, fn, _writes_enabled) -> None:
    """Each tool, when invoked, should call its underlying SDK function exactly once."""
    module_path = module.__name__  # e.g. "robin_stocks.robinhood"
    with patch(f"{module_path}.{attr}", return_value={"ok": True}) as sdk_mock:
        kwargs = _build_kwargs(fn)
        await fn(**kwargs)

    # The SDK function must have been called. (Some tools post-process the
    # result into a string, so we don't assert on the return value.)
    assert sdk_mock.called, f"{name} did not call {module_path}.{attr}"
