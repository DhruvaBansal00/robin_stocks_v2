"""Verify that every tool module registers tools with the FastMCP instance, and that
each registered tool has the right name prefix, an input schema, and a docstring."""

from __future__ import annotations

from robin_stocks_mcp.app import mcp

EXPECTED_PREFIXES = {"rh_", "tda_", "gem_"}


def _all_tools():
    return mcp._tool_manager.list_tools()


def test_at_least_180_tools_registered() -> None:
    """If we ever lose a module, the count will drop sharply."""
    assert len(_all_tools()) >= 180, f"only {len(_all_tools())} tools registered"


def test_every_tool_has_known_prefix() -> None:
    bad = [t.name for t in _all_tools() if not any(t.name.startswith(p) for p in EXPECTED_PREFIXES)]
    assert not bad, f"tools missing broker prefix: {bad}"


def test_every_tool_has_description() -> None:
    bad = [t.name for t in _all_tools() if not (t.description or "").strip()]
    assert not bad, f"tools missing description: {bad}"


def test_every_tool_has_input_schema() -> None:
    bad = [t.name for t in _all_tools() if not isinstance(t.parameters, dict)]
    assert not bad, f"tools missing input schema: {bad}"


def test_no_duplicate_tool_names() -> None:
    names = [t.name for t in _all_tools()]
    assert len(names) == len(set(names)), "duplicate tool names registered"


def test_login_tools_present() -> None:
    names = {t.name for t in _all_tools()}
    for required in ("rh_login", "rh_logout", "tda_login", "gem_login"):
        assert required in names, f"missing required tool: {required}"
