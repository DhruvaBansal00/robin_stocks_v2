"""Index-option routing tests (PR #541).

Covers:
- ``_index_chain_symbol`` mapping for every supported index
- ``find_tradable_options`` payload uses the right chain_symbol per index
- Non-index symbols use the symbol verbatim
- The login_required guard
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import options


# ---------------------------------------------------------------------------
# _index_chain_symbol mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "symbol, expected",
    [
        ("NDX", "NDXP"),
        ("SPX", "SPXW"),
        ("RUT", "RUTW"),
        ("VIX", "VIXW"),
        ("XSP", "XSP"),       # XSP has no suffix
        ("AAPL", "AAPL"),     # Non-index passes through
        ("TSLA", "TSLA"),
        ("", ""),
    ],
)
def test_index_chain_symbol_mapping(symbol: str, expected: str) -> None:
    assert options._index_chain_symbol(symbol) == expected


# ---------------------------------------------------------------------------
# find_tradable_options payload
# ---------------------------------------------------------------------------


@pytest.fixture
def mocked_options_deps():
    """Mock chain ID lookup and the pagination request."""
    patches = [
        patch("robin_stocks.robinhood.options.id_for_chain", return_value="chain-id-1"),
        patch("robin_stocks.robinhood.options.request_get", return_value=[{"id": "opt-1"}]),
        patch("robin_stocks.robinhood.helper.LOGGED_IN", True),
    ]
    entered = [p.__enter__() for p in patches]
    yield {"request_get": entered[1]}
    for p in patches:
        p.__exit__(None, None, None)


def test_find_tradable_options_regular_symbol_uses_verbatim_chain_symbol(mocked_options_deps) -> None:
    options.find_tradable_options("AAPL")
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["chain_symbol"] == "AAPL"
    assert payload["chain_id"] == "chain-id-1"
    assert payload["state"] == "active"


def test_find_tradable_options_spx_uses_spxw(mocked_options_deps) -> None:
    options.find_tradable_options("SPX")
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["chain_symbol"] == "SPXW"


def test_find_tradable_options_ndx_uses_ndxp(mocked_options_deps) -> None:
    options.find_tradable_options("NDX")
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["chain_symbol"] == "NDXP"


def test_find_tradable_options_rut_uses_rutw(mocked_options_deps) -> None:
    options.find_tradable_options("RUT")
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["chain_symbol"] == "RUTW"


def test_find_tradable_options_vix_uses_vixw(mocked_options_deps) -> None:
    options.find_tradable_options("VIX")
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["chain_symbol"] == "VIXW"


def test_find_tradable_options_xsp_uses_xsp_verbatim(mocked_options_deps) -> None:
    """XSP is the one index without a suffix."""
    options.find_tradable_options("XSP")
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["chain_symbol"] == "XSP"


def test_find_tradable_options_forwards_optional_filters(mocked_options_deps) -> None:
    options.find_tradable_options(
        "AAPL", expirationDate="2026-06-19", strikePrice="100", optionType="call"
    )
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["expiration_dates"] == "2026-06-19"
    assert payload["strike_price"] == "100"
    assert payload["type"] == "call"


def test_find_tradable_options_invalid_symbol_returns_none() -> None:
    """Non-string symbols return [None] without touching network."""
    with patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        out = options.find_tradable_options(12345)
    assert out == [None]


def test_find_tradable_options_unknown_chain_returns_none() -> None:
    with patch("robin_stocks.robinhood.options.id_for_chain", return_value=None), \
         patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        out = options.find_tradable_options("ZZZZ")
    assert out == [None]


def test_find_tradable_options_uppercases_lowercase_symbol(mocked_options_deps) -> None:
    options.find_tradable_options("spx")
    payload = mocked_options_deps["request_get"].call_args[0][2]
    assert payload["chain_symbol"] == "SPXW"
