"""
Unit Tests for Cryptographically Signed Revocation Events & Sequence Validation.
"""

import pytest

from guardwaf.control_plane.events.events import (
    EventSequenceValidator,
    EventSignatureVerifier,
)
from guardwaf.core.keys import KeyManager
from guardwaf.exceptions import GuardWAFSecurityError
from guardwaf.sdk.revocation_client import RevocationClient


def test_signed_revocation_event_creation_and_verification():
    km = KeyManager(secret_key="secret_key_signed_test")
    verifier = EventSignatureVerifier(key_manager=km)

    signed_event = verifier.sign_event("AGENT_REVOKED", "tenant_1", sequence_number=1, agent_id="bot_bad")
    assert verifier.verify_event_signature(signed_event) is True


def test_forged_revocation_event_rejection():
    km = KeyManager(secret_key="secret_key_signed_test")
    verifier = EventSignatureVerifier(key_manager=km)

    signed_event = verifier.sign_event("AGENT_REVOKED", "tenant_1", sequence_number=1, agent_id="bot_bad")

    # Tamper signature
    signed_event.signature = "forged_signature_hex"
    assert verifier.verify_event_signature(signed_event) is False


def test_sequence_number_anti_replay():
    validator = EventSequenceValidator()

    # Sequence 1: Valid
    assert validator.is_valid_sequence("tenant_1", 1, "agent_1") is True
    # Sequence 2: Valid
    assert validator.is_valid_sequence("tenant_1", 2, "agent_1") is True
    # Replayed Sequence 1: Invalid!
    assert validator.is_valid_sequence("tenant_1", 1, "agent_1") is False


def test_revocation_client_integration():
    km = KeyManager(secret_key="secret_key_revocation_test")
    verifier = EventSignatureVerifier(key_manager=km)
    client = RevocationClient(key_manager=km)

    event = verifier.sign_event("AGENT_REVOKED", "tenant_x", sequence_number=10, agent_id="rogue_bot")
    applied = client.process_signed_event(event)
    assert applied is True

    with pytest.raises(GuardWAFSecurityError) as exc_info:
        client.check_kill_switch_local("tenant_x", "rogue_bot")
    assert "REVOKED" in exc_info.value.message
