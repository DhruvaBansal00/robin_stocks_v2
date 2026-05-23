"""Runtime helpers: thread offload, error formatting, read-only guard."""

from __future__ import annotations

import asyncio
import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import requests

from .config import Config, load_config

T = TypeVar("T")

# Module-level singletons
_config: Config = load_config()


def get_config() -> Config:
    return _config


def set_config(cfg: Config) -> None:
    global _config
    _config = cfg


class ReadOnlyError(RuntimeError):
    """Raised when a write-operation tool is invoked while the server is in read-only mode."""


def require_writes_allowed(tool_name: str) -> None:
    """Block destructive tools when read-only mode is on."""
    if _config.read_only:
        raise ReadOnlyError(
            f"Tool '{tool_name}' performs a write/trade/transfer action and is blocked because "
            "ROBIN_STOCKS_MCP_READ_ONLY=true (default). Set ROBIN_STOCKS_MCP_READ_ONLY=false to enable."
        )


async def to_thread(func: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Run blocking SDK calls off the event loop."""
    return await asyncio.to_thread(func, *args, **kwargs)


def format_error(exc: BaseException) -> dict[str, Any]:
    """Render an exception as a JSON-friendly object."""
    return {
        "error": True,
        "type": type(exc).__name__,
        "message": str(exc),
    }


def _coerce_response(value: Any) -> Any:
    """Parse a raw ``requests.Response`` into JSON, falling back to status/text."""
    if isinstance(value, requests.Response):
        try:
            return value.json()
        except ValueError:
            return {"status_code": value.status_code, "text": value.text}
    return value


def normalize_result(value: Any) -> Any:
    """Make an SDK return value JSON-serializable for the MCP transport.

    The Gemini and TDA SDK functions return a ``(data, error)`` tuple, and when their
    parse-json default is off (it is, by default) ``data`` is a raw ``requests.Response`` —
    which serializes to the useless string ``"<Response [200]>"``. Robinhood instead returns
    parsed data directly. This normalizes every shape: it unpacks the ``(data, error)`` tuple,
    surfaces an SDK error as a structured payload, and parses any raw Response into JSON.

    A 2-tuple is only treated as ``(data, error)`` when its second element is ``None`` or an
    exception, so genuine 2-element data (e.g. a Robinhood list) passes through untouched.
    """
    if isinstance(value, tuple) and len(value) == 2 and (value[1] is None or isinstance(value[1], BaseException)):
        data, error = value
        if error is not None:
            return format_error(error)
        return _coerce_response(data)
    return _coerce_response(value)


def safe_tool(write: bool = False) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorator: catch exceptions and (optionally) enforce read-only mode.

    Tools decorated with `write=True` will be blocked when the server runs in read-only mode.
    Any uncaught exception is converted into a structured error payload so the client can
    surface the failure to the model without crashing the MCP transport.
    """

    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                if write:
                    require_writes_allowed(fn.__name__)
                result = fn(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result
                return normalize_result(result)
            except ReadOnlyError as e:
                return format_error(e)
            except Exception as e:  # noqa: BLE001 - tool surface boundary
                return format_error(e)

        return wrapper

    return decorator
