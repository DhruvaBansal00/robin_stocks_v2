"""End-to-end test: spawn the server as a subprocess over STDIO and round-trip MCP messages.

This is the highest-fidelity test we can do offline — it confirms the entire pipeline
(install entry point → argparse → FastMCP → JSON-RPC over stdio) actually works.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _send(proc: subprocess.Popen, msg: dict) -> None:
    assert proc.stdin is not None
    line = json.dumps(msg) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()


def _recv(proc: subprocess.Popen, timeout_s: float = 10.0) -> dict:
    assert proc.stdout is not None
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.05)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            # FastMCP sometimes prints log lines on stdout; skip until JSON
            continue
    raise TimeoutError("server did not respond")


@pytest.mark.timeout(30)
def test_server_subprocess_lists_tools() -> None:
    env = os.environ.copy()
    env.setdefault("ROBIN_STOCKS_MCP_AUTO_LOGIN", "false")  # don't dial out
    env.setdefault("ROBIN_STOCKS_MCP_READ_ONLY", "true")

    proc = subprocess.Popen(
        [sys.executable, "-m", "robin_stocks_mcp.server", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    try:
        # MCP handshake
        _send(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        })
        init_resp = _recv(proc)
        assert init_resp.get("id") == 1
        assert "result" in init_resp, init_resp

        # Required `notifications/initialized` after initialize
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        # List tools
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        list_resp = _recv(proc)
        assert list_resp.get("id") == 2
        tools = list_resp["result"]["tools"]
        names = {t["name"] for t in tools}
        assert "rh_get_quotes" in names
        assert "tda_get_quote" in names
        assert "gem_get_pubticker" in names
        assert len(tools) >= 180
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


@pytest.mark.timeout(30)
def test_server_subprocess_blocks_write_in_read_only() -> None:
    """Calling a write-guarded tool over real STDIO should come back as an error payload,
    not crash the server."""
    env = os.environ.copy()
    env["ROBIN_STOCKS_MCP_AUTO_LOGIN"] = "false"
    env["ROBIN_STOCKS_MCP_READ_ONLY"] = "true"

    proc = subprocess.Popen(
        [sys.executable, "-m", "robin_stocks_mcp.server", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    try:
        _send(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        })
        _recv(proc)
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        _send(proc, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "rh_order_buy_market",
                "arguments": {"symbol": "AAPL", "quantity": 1},
            },
        })
        resp = _recv(proc, timeout_s=15.0)
        # FastMCP returns either an isError result or an error payload; either way the
        # server must surface ReadOnlyError without crashing.
        body = json.dumps(resp)
        assert "ReadOnlyError" in body, body
        assert resp.get("id") == 2
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
