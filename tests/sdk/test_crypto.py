"""Crypto position tests — focuses on the PR #333 addition.

``get_open_crypto_positions`` must hit the same URL as ``get_crypto_positions``
but with ``nonzero=true`` as the payload.
"""

from __future__ import annotations

from unittest.mock import patch

from robin_stocks.robinhood import crypto


def test_get_open_crypto_positions_sends_nonzero_flag() -> None:
    """PR #333: the open-positions endpoint differs from the full list only
    by the nonzero=true payload."""
    with patch("robin_stocks.robinhood.crypto.request_get", return_value=[{"currency": "BTC"}]) as rg, \
         patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        out = crypto.get_open_crypto_positions()

    # URL must be the crypto holdings endpoint
    assert rg.call_args[0][0] == "https://nummus.robinhood.com/holdings/"
    # Pagination mode and the nonzero filter must be present
    assert rg.call_args[0][1] == "pagination"
    assert rg.call_args[0][2] == {"nonzero": "true"}
    assert out == [{"currency": "BTC"}]


def test_get_open_crypto_positions_filters_by_info() -> None:
    payload = [{"currency": "BTC", "quantity": "1"}, {"currency": "ETH", "quantity": "2"}]
    with patch("robin_stocks.robinhood.crypto.request_get", return_value=payload), \
         patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        out = crypto.get_open_crypto_positions(info="currency")
    assert out == ["BTC", "ETH"]


def test_get_crypto_positions_does_not_filter_by_nonzero() -> None:
    """The full-list endpoint must NOT pass nonzero (regression for #333)."""
    with patch("robin_stocks.robinhood.crypto.request_get", return_value=[]) as rg, \
         patch("robin_stocks.robinhood.helper.LOGGED_IN", True):
        crypto.get_crypto_positions()

    # Confirm get_crypto_positions calls without the nonzero payload
    args = rg.call_args
    # The function signature is request_get(url, 'pagination'), so only 2 positional
    assert len(args[0]) == 2
    assert args[0][1] == "pagination"
