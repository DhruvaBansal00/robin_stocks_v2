"""Tests for the runtime helpers: thread offload, read-only guard, error capture."""

from __future__ import annotations

import asyncio

import pytest

from robin_stocks_mcp import runtime
from robin_stocks_mcp.runtime import ReadOnlyError, format_error, safe_tool, to_thread


def test_format_error_shape() -> None:
    err = ValueError("nope")
    out = format_error(err)
    assert out == {"error": True, "type": "ValueError", "message": "nope"}


def test_to_thread_runs_blocking_call() -> None:
    import threading

    main_tid = threading.get_ident()

    def blocking() -> int:
        return threading.get_ident()

    result_tid = asyncio.run(to_thread(blocking))
    assert result_tid != main_tid


def test_safe_tool_catches_exceptions() -> None:
    @safe_tool()
    async def boom() -> None:
        raise RuntimeError("kaboom")

    out = asyncio.run(boom())
    assert out["error"] is True
    assert out["type"] == "RuntimeError"
    assert "kaboom" in out["message"]


def test_safe_tool_passes_through_success() -> None:
    @safe_tool()
    async def ok(x: int) -> int:
        return x + 1

    assert asyncio.run(ok(x=2)) == 3


def test_safe_tool_write_blocked_in_read_only(writes_disabled: None) -> None:
    @safe_tool(write=True)
    async def write_op() -> str:
        return "wrote"

    out = asyncio.run(write_op())
    assert out["error"] is True
    assert out["type"] == "ReadOnlyError"


def test_safe_tool_write_allowed_when_enabled(writes_enabled: None) -> None:
    @safe_tool(write=True)
    async def write_op() -> str:
        return "wrote"

    assert asyncio.run(write_op()) == "wrote"


def test_safe_tool_handles_sync_function() -> None:
    @safe_tool()
    def sync_fn(x: int) -> int:
        return x * 2

    # safe_tool returns an async wrapper regardless; awaiting it should work.
    assert asyncio.run(sync_fn(x=3)) == 6


def test_require_writes_allowed_raises_when_read_only(writes_disabled: None) -> None:
    with pytest.raises(ReadOnlyError):
        runtime.require_writes_allowed("x")


def test_require_writes_allowed_silent_when_enabled(writes_enabled: None) -> None:
    runtime.require_writes_allowed("x")  # must not raise
