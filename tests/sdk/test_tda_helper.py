"""Regression tests for robin_stocks.tda.helper.format_inputs."""

from __future__ import annotations

from robin_stocks.tda import helper


def _decorated():
    @helper.format_inputs
    def fn(ticker, jsonify=None):
        return ticker, jsonify

    return fn


def test_format_inputs_positional_none_jsonify_no_duplicate_arg() -> None:
    """Regression: passing jsonify=None positionally must not raise
    'got multiple values for argument jsonify'."""
    fn = _decorated()
    ticker, jsonify = fn("AAPL", None)
    assert ticker == "AAPL"
    assert jsonify == helper.get_default_json_flag()


def test_format_inputs_keyword_none_jsonify_uses_default() -> None:
    fn = _decorated()
    assert fn("AAPL", jsonify=None)[1] == helper.get_default_json_flag()


def test_format_inputs_explicit_jsonify_preserved() -> None:
    fn = _decorated()
    assert fn("AAPL", jsonify=False)[1] is False
