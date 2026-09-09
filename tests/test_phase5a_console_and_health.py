"""
Phase 5A Unit Test Suite for Console Services, JWT Auth, SSE Event Stream, Health Metrics, and Tenant Lockdown.
"""

import pytest
from fastapi.testclient import TestClient

from guardwaf.control_plane.app import create_control_plane_app
from guardwaf.control_plane.auth.jwt import create_jwt_token, verify_jwt_token
from guardwaf.control_plane.events.sse import SSEBroadcaster
from guardwaf.db.migrations import DatabaseMigrationManager
from guardwaf.exceptions import GuardWAFSecurityError

# ============================================================================
# 1. JWT AUTHENTICATION TESTS
# ============================================================================


def test_jwt_token_generation_and_verification():
    token = create_jwt_token(
        user_id="usr_123",
        email="test@acme.com",
        organization_id="org_acme",
        role="SECURITY_ADMIN",
    )
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    payload = verify_jwt_token(token)
    assert payload["sub"] == "usr_123"
    assert payload["email"] == "test@acme.com"
    assert payload["org_id"] == "org_acme"
    assert payload["role"] == "SECURITY_ADMIN"


def test_jwt_invalid_signature_rejection():
    token = create_jwt_token("usr_123", "test@acme.com", "org_acme", "ADMIN", secret_key="key_1")
    with pytest.raises(GuardWAFSecurityError) as exc:
        verify_jwt_token(token, secret_key="key_2")
    assert "Invalid JWT signature" in exc.value.message


# ============================================================================
# 2. SSE EVENT BROADCASTER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_sse_broadcaster_subscribe_and_broadcast():
    broadcaster = SSEBroadcaster()
    queue = broadcaster.subscribe("org_test")

    event = {
        "event_type": "ACTION_BLOCKED",
        "agent_id": "agent_x",
        "parameters": {"ssn": "123-45-6789", "amount": 100},
    }
    await broadcaster.broadcast_event("org_test", event)

    received = await queue.get()
    assert received["event_type"] == "ACTION_BLOCKED"
    # Verify sensitive parameter 'ssn' was redacted by SSE broadcaster
    assert received["parameters"]["ssn"] == "[REDACTED]"


# ============================================================================
# 3. DATABASE MIGRATION TESTS
# ============================================================================


def test_database_migration_manager():
    mgr = DatabaseMigrationManager()
    assert mgr.get_current_version() == 0

    applied = mgr.apply_pending_migrations()
    assert len(applied) == 2
    assert mgr.get_current_version() == 2


# ============================================================================
# 4. HEALTH & OBSERVABILITY ENDPOINT TESTS
# ============================================================================


def test_health_and_metrics_endpoints():
    app = create_control_plane_app()
    client = TestClient(app)

    r_live = client.get("/health/live")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "LIVE"

    r_ready = client.get("/health/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "READY"

    r_metrics = client.get("/metrics")
    assert r_metrics.status_code == 200
    assert "guardwaf_control_plane_requests_total" in r_metrics.text
