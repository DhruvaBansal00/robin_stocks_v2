"""Tests for the runtime helpers: thread offload, read-only guard, error capture."""

from __future__ import annotations

import asyncio
from unittest.mock import Mock

import pytest
import requests

from robin_stocks_mcp import runtime
from robin_stocks_mcp.runtime import ReadOnlyError, format_error, normalize_result, safe_tool, to_thread


def _fake_response(json_value: object = None, *, raises: bool = False, status_code: int = 200, text: str = "") -> Mock:
    """Build a stand-in for requests.Response with a controllable .json()."""
    resp = Mock(spec=requests.Response)
    resp.status_code = status_code
    resp.text = text
    if raises:
        resp.json.side_effect = ValueError("no json")
    else:
        resp.json.return_value = json_value
    return resp


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


# --- normalize_result: the (data, error) tuple + raw Response handling ---


def test_normalize_unwraps_data_error_tuple() -> None:
    assert normalize_result(({"last": "1"}, None)) == {"last": "1"}


def test_normalize_parses_response_inside_tuple() -> None:
    resp = _fake_response({"symbol": "btcusd"})
    assert normalize_result((resp, None)) == {"symbol": "btcusd"}


def test_normalize_surfaces_sdk_error_from_tuple() -> None:
    out = normalize_result((None, ValueError("bad request")))
    assert out == {"error": True, "type": "ValueError", "message": "bad request"}


def test_normalize_parses_bare_response() -> None:
    assert normalize_result(_fake_response([1, 2, 3])) == [1, 2, 3]


def test_normalize_non_json_response_falls_back_to_status_text() -> None:
    resp = _fake_response(raises=True, status_code=503, text="unavailable")
    assert normalize_result(resp) == {"status_code": 503, "text": "unavailable"}


@pytest.mark.parametrize(
    "value",
    [
        {"a": 1},
        ["x", "y"],
        None,
        "plain string",
        ["data", "not-an-error"],  # 2-element list, not a (data, error) tuple
    ],
)
def test_normalize_passes_through_plain_values(value: object) -> None:
    # Robinhood already returns parsed data directly; it must be left untouched.
    assert normalize_result(value) == value


def test_safe_tool_normalizes_response_tuple() -> None:
    resp = _fake_response({"ok": True})

    @safe_tool()
    async def fetch() -> object:
        return resp, None

    assert asyncio.run(fetch()) == {"ok": True}
