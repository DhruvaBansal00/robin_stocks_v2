"""Dispatch tests for tools excluded from the generic dispatch sweep:
the document-download tools (bespoke return strings) and the TDA auth tools.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks_mcp.app import mcp


def get_fn(name: str):
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None, f"tool '{name}' not registered"
    return tool.fn


# ---------------------------------------------------------------------------
# Document downloads (write tools)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rh_download_document_blocked_read_only(writes_disabled) -> None:
    with patch("robin_stocks.robinhood.download_document") as m:
        out = await get_fn("rh_download_document")(url="https://x/doc/1/")
        assert out["error"] is True
        m.assert_not_called()


@pytest.mark.asyncio
async def test_rh_download_document_dispatches(writes_enabled) -> None:
    with patch("robin_stocks.robinhood.download_document") as m:
        out = await get_fn("rh_download_document")(url="https://x/doc/1/", name="doc", dirpath="/tmp")
        m.assert_called_once_with("https://x/doc/1/", name="doc", dirpath="/tmp")
        assert out.startswith("ok:")


@pytest.mark.asyncio
async def test_rh_download_all_documents_dispatches(writes_enabled) -> None:
    with patch("robin_stocks.robinhood.download_all_documents") as m:
        out = await get_fn("rh_download_all_documents")(doctype="trade_confirm", dirpath="/tmp")
        m.assert_called_once_with(doctype="trade_confirm", dirpath="/tmp")
        assert out.startswith("ok:")


# ---------------------------------------------------------------------------
# TDA auth tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tda_login_dispatches() -> None:
    with patch("robin_stocks.tda.login") as m:
        out = await get_fn("tda_login")(encryption_passcode="pc")
        m.assert_called_once_with("pc")
        assert "TDA login" in out


@pytest.mark.asyncio
async def test_tda_login_first_time_dispatches() -> None:
    with patch("robin_stocks.tda.login_first_time") as m:
        out = await get_fn("tda_login_first_time")(
            encryption_passcode="pc", client_id="cid",
            authorization_token="auth", refresh_token="ref",
        )
        m.assert_called_once_with("pc", "cid", "auth", "ref")
        assert "saved" in out


@pytest.mark.asyncio
async def test_tda_generate_encryption_passcode_dispatches() -> None:
    with patch("robin_stocks.tda.generate_encryption_passcode", return_value="generated-key") as m:
        out = await get_fn("tda_generate_encryption_passcode")()
        m.assert_called_once_with()
        assert out == "generated-key"
