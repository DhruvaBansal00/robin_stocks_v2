"""Tests for _validate_sherrif_id — Robinhood's device-verification polling flow.

This is the security-sensitive challenge/response loop triggered when a login
needs SMS/email/app approval. We drive it with mocked network + time so the
polling loops terminate deterministically.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from robin_stocks.robinhood import authentication as auth


@pytest.fixture
def no_sleep():
    with patch("robin_stocks.robinhood.authentication.time.sleep"):
        yield


def test_validate_sherrif_id_prompt_challenge_validated(no_sleep) -> None:
    """App-prompt challenge: poll until prompt status is 'validated', then the
    workflow status confirms approval."""
    machine_response = {"id": "machine-1"}
    inquiry_with_prompt = {"context": {"sheriff_challenge": {"type": "prompt", "status": "issued", "id": "ch-1"}}}
    prompt_validated = {"challenge_status": "validated"}
    workflow_approved = {"type_context": {"result": "workflow_status_approved"}}

    with (
        patch("robin_stocks.robinhood.authentication.request_post", side_effect=[machine_response, workflow_approved]) as rp,
        patch("robin_stocks.robinhood.authentication.request_get", side_effect=[inquiry_with_prompt, prompt_validated]),
    ):
        # Should complete without raising
        auth._validate_sherrif_id("device-tok", "workflow-1")

    assert rp.call_count >= 1


def test_validate_sherrif_id_sms_challenge(no_sleep) -> None:
    """SMS challenge: user enters a code, the challenge validates, then workflow approves."""
    machine_response = {"id": "machine-1"}
    inquiry_sms = {"context": {"sheriff_challenge": {"type": "sms", "status": "issued", "id": "ch-1"}}}
    workflow_approved = {"type_context": {"result": "workflow_status_approved"}}

    with (
        patch(
            "robin_stocks.robinhood.authentication.request_post",
            side_effect=[machine_response, {"status": "validated"}, workflow_approved],
        ),
        patch("robin_stocks.robinhood.authentication.request_get", side_effect=[inquiry_sms]),
        patch("builtins.input", return_value="123456"),
    ):
        auth._validate_sherrif_id("device-tok", "workflow-1")


def test_validate_sherrif_id_validated_status_breaks_loop(no_sleep) -> None:
    """A challenge already in 'validated' status short-circuits the first loop."""
    machine_response = {"id": "machine-1"}
    inquiry_validated = {"context": {"sheriff_challenge": {"type": "other", "status": "validated", "id": "ch-1"}}}
    workflow_approved = {"type_context": {"result": "workflow_status_approved"}}

    with (
        patch("robin_stocks.robinhood.authentication.request_post", side_effect=[machine_response, workflow_approved]),
        patch("robin_stocks.robinhood.authentication.request_get", side_effect=[inquiry_validated]),
    ):
        auth._validate_sherrif_id("device-tok", "workflow-1")


def test_validate_sherrif_id_raises_when_no_machine_id(no_sleep) -> None:
    """If the pathfinder response lacks an id, _get_sherrif_id raises."""
    with patch("robin_stocks.robinhood.authentication.request_post", return_value={"no": "id"}):
        with pytest.raises(Exception, match="No verification ID"):
            auth._validate_sherrif_id("device-tok", "workflow-1")


def test_validate_sherrif_id_workflow_status_field_approves(no_sleep) -> None:
    """After a challenge breaks the first loop, the workflow poll can approve via
    the verification_workflow.workflow_status field (rather than type_context)."""
    machine_response = {"id": "machine-1"}
    inquiry_validated = {"context": {"sheriff_challenge": {"type": "other", "status": "validated", "id": "ch-1"}}}
    # No type_context key → falls through to the workflow_status check
    workflow_via_status = {"verification_workflow": {"workflow_status": "workflow_status_approved"}}

    with (
        patch("robin_stocks.robinhood.authentication.request_post", side_effect=[machine_response, workflow_via_status]),
        patch("robin_stocks.robinhood.authentication.request_get", side_effect=[inquiry_validated]),
    ):
        auth._validate_sherrif_id("device-tok", "workflow-1")
