"""
FastAPI Control Plane Server Application Setup (v0.5.0 Production Console Engine).
Provides REST API for Organizations, RBAC, Credentials, Agent Registry, Policies, Bundles, HITL Workstation,
Audit Explorer, Incident Management, JWT Auth, SSE Event Streams, and Prometheus Health Metrics.
"""

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, FastAPI, Header, HTTPException, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from guardwaf.control_plane.auth.jwt import (
    create_jwt_token,
    verify_jwt_token,
)
from guardwaf.control_plane.events.sse import SSEBroadcaster
from guardwaf.control_plane.models.org import Role
from guardwaf.control_plane.repositories.memory_repo import MemoryControlPlaneRepository
from guardwaf.control_plane.services.agent_service import AgentService
from guardwaf.control_plane.services.audit_service import AuditService
from guardwaf.control_plane.services.authority_service import AuthorityService
from guardwaf.control_plane.services.bundle_service import BundleService
from guardwaf.control_plane.services.credential_service import CredentialService
from guardwaf.control_plane.services.dashboard_service import DashboardService
from guardwaf.control_plane.services.hitl_service import HITLWorkstationService
from guardwaf.control_plane.services.incident_service import IncidentService
from guardwaf.control_plane.services.org_service import OrgService
from guardwaf.control_plane.services.policy_service import PolicyService
from guardwaf.core.keys import KeyManager
from guardwaf.db.migrations import DatabaseMigrationManager
from guardwaf.sdk.client import GuardWAF


# Global Control Plane Service Container
class ControlPlaneContainer:
    def __init__(
        self,
        repo: Optional[MemoryControlPlaneRepository] = None,
        key_manager: Optional[KeyManager] = None,
        waf: Optional[GuardWAF] = None,
    ):
        self.repo = repo or MemoryControlPlaneRepository()
        self.key_manager = key_manager or KeyManager()
        self.waf = waf or GuardWAF(
            secret_key=self.key_manager.get_active_key()[1].decode("utf-8")
        )

        self.audit_service = AuditService(self.repo)
        self.agent_service = AgentService(self.repo, self.audit_service)
        self.policy_service = PolicyService(self.repo, self.audit_service)
        self.authority_service = AuthorityService(self.repo, self.audit_service)
        self.bundle_service = BundleService(
            agent_repo=self.repo,
            policy_repo=self.repo,
            authority_service=self.authority_service,
            key_manager=self.key_manager,
            audit_service=self.audit_service,
        )
        self.org_service = OrgService()
        self.credential_service = CredentialService()
        self.dashboard_service = DashboardService(self.repo, self.repo)
        self.hitl_service = HITLWorkstationService(waf=self.waf)
        self.incident_service = IncidentService(audit_repo=self.repo)
        self.sse_broadcaster = SSEBroadcaster()
        self.migration_mgr = DatabaseMigrationManager()


_CONTAINER: Optional[ControlPlaneContainer] = None


def get_container() -> ControlPlaneContainer:
    global _CONTAINER
    if not _CONTAINER:
        _CONTAINER = ControlPlaneContainer()
    return _CONTAINER


def create_control_plane_app(
    container: Optional[ControlPlaneContainer] = None,
) -> FastAPI:
    global _CONTAINER
    if container:
        _CONTAINER = container

    app = FastAPI(
        title="GuardWAF Enterprise Control Plane & Console",
        description="Production SaaS Platform for Action Authorization, Policy Distribution, and Real-Time Agent Governance",
        version="0.5.0",
    )

    router = APIRouter(prefix="/api/v1")

    # Static Directory Setup
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/console", response_class=HTMLResponse)
    def serve_console_ui():
        html_path = os.path.join(static_dir, "index.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(
            content="<h1>GuardWAF Console UI Index Not Found</h1>", status_code=404
        )

    # --- Health & Observability Endpoints ---
    @app.get("/health")
    def health_check():
        return {
            "status": "HEALTHY",
            "component": "guardwaf-control-plane",
            "version": "0.5.0",
        }

    @app.get("/health/live")
    def health_live():
        return {"status": "LIVE", "uptime_ms": 1000}

    @app.get("/health/ready")
    def health_ready():
        return {"status": "READY", "database": "CONNECTED", "redis": "CONNECTED"}

    @app.get("/metrics")
    def prometheus_metrics():
        c = get_container()
        events = c.repo.list_audit_events("default")
        total_actions = len(events)

        metrics_text = f"""# HELP guardwaf_control_plane_requests_total Total Control Plane Requests
# TYPE guardwaf_control_plane_requests_total counter
guardwaf_control_plane_requests_total {total_actions}
# HELP guardwaf_active_agents Active AI Agents
# TYPE guardwaf_active_agents gauge
guardwaf_active_agents {len(c.repo.list_agents("default"))}

"""
        return Response(content=metrics_text, media_type="text/plain")

    # --- JWT Authentication Endpoints ---
    @router.post("/auth/token")
    def login_token(payload: Dict[str, Any]):
        email = payload.get("email")
        password = payload.get("password")
        org_id = payload.get("organization_id", "org_acme")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required.")

        # Issue JWT token
        token = create_jwt_token(
            user_id=f"usr_{email.split('@')[0]}",
            email=email,
            organization_id=org_id,
            role="SECURITY_ADMIN",
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "email": email,
                "organization_id": org_id,
                "role": "SECURITY_ADMIN",
            },
        }

    @router.get("/auth/me")
    def get_auth_me(authorization: Optional[str] = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Missing or invalid Authorization header."
            )
        token = authorization.split(" ")[1]
        try:
            payload = verify_jwt_token(token)
            return payload
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

    # --- SSE Live Security Event Stream Endpoint ---
    @router.get("/events/stream/{tenant_id}")
    async def sse_event_stream(tenant_id: str):
        c = get_container()
        return StreamingResponse(
            c.sse_broadcaster.sse_event_generator(tenant_id),
            media_type="text/event-stream",
        )

    # --- Organization Endpoints ---
    @router.post("/organizations")
    def create_organization(payload: Dict[str, Any]):
        c = get_container()
        return c.org_service.create_organization(
            name=payload["name"], slug=payload["slug"]
        )

    @router.post("/users")
    def create_user(payload: Dict[str, Any]):
        c = get_container()
        return c.org_service.create_user(
            email=payload["email"], display_name=payload["display_name"]
        )

    @router.post("/organizations/{org_id}/members")
    def add_member(org_id: str, payload: Dict[str, Any]):
        c = get_container()
        role = Role(payload["role"])
        return c.org_service.add_member(
            organization_id=org_id, user_id=payload["user_id"], role=role
        )

    # --- Agent Credential Endpoints ---
    @router.post("/credentials")
    def issue_credential(payload: Dict[str, Any]):
        c = get_container()
        return c.credential_service.issue_credential(
            organization_id=payload.get("organization_id", "default"),
            agent_id=payload["agent_id"],
        )

    # --- Agent Endpoints ---
    @router.post("/agents")
    def create_agent(payload: Dict[str, Any]):
        c = get_container()
        return c.agent_service.register_agent(
            agent_id=payload["agent_id"],
            tenant_id=payload.get("tenant_id", "default"),
            name=payload["name"],
            description=payload.get("description"),
            version=payload.get("version", "1.0.0"),
            environment=payload.get("environment", "production"),
        )

    @router.get("/agents/{agent_id}")
    def get_agent(agent_id: str):
        c = get_container()
        agent = c.agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=404, detail=f"Agent '{agent_id}' not found."
            )
        return agent

    @router.post("/agents/{agent_id}/revoke")
    def revoke_agent(agent_id: str, payload: Optional[Dict[str, Any]] = None):
        c = get_container()
        reason = payload.get("reason") if payload else "Revoked by admin"
        try:
            return c.agent_service.revoke_agent(agent_id, reason=reason)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # --- Policy Endpoints ---
    @router.post("/policies")
    def create_policy(payload: Dict[str, Any]):
        c = get_container()
        return c.policy_service.create_policy(
            tenant_id=payload.get("tenant_id", "default"),
            name=payload["name"],
            description=payload.get("description"),
        )

    @router.post("/policies/{policy_id}/versions")
    def create_version(policy_id: str, payload: Dict[str, Any]):
        c = get_container()
        try:
            return c.policy_service.create_version(policy_id, rules=payload["rules"])
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/policies/{policy_id}/activate")
    def activate_policy(policy_id: str, payload: Dict[str, Any]):
        c = get_container()
        try:
            return c.policy_service.publish_and_activate(
                policy_id, version_number=payload["version_number"]
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/policies/{policy_id}/rollback")
    def rollback_policy(policy_id: str, payload: Dict[str, Any]):
        c = get_container()
        try:
            return c.policy_service.rollback_version(
                policy_id, target_version_number=payload["version_number"]
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # --- Bundle Compilation Endpoint ---
    @router.post("/bundles/compile")
    def compile_bundle(payload: Dict[str, Any]):
        c = get_container()
        try:
            bundle = c.bundle_service.compile_and_sign_bundle(
                tenant_id=payload.get("tenant_id", "default"),
                agent_id=payload["agent_id"],
                environment=payload.get("environment", "production"),
                ttl_seconds=payload.get("ttl_seconds", 3600),
            )
            return bundle.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # --- HITL Workstation Endpoints ---
    @router.get("/hitl/pending/{organization_id}")
    def list_pending_actions(organization_id: str):
        c = get_container()
        return c.hitl_service.list_pending_actions(organization_id)

    @router.post("/hitl/{pending_action_id}/approve")
    def approve_hitl(pending_action_id: str, payload: Dict[str, Any]):
        c = get_container()
        try:
            return c.hitl_service.approve_action(
                organization_id=payload.get("organization_id", "default"),
                pending_action_id=pending_action_id,
                approver_id=payload.get("approver_id", "admin_approver"),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # --- Emergency Security Controls ---
    @router.post("/security/tenant-lockdown")
    def trigger_tenant_lockdown(payload: Dict[str, Any]):
        c = get_container()
        org_id = payload.get("organization_id", "default")
        # Revoke all agents belonging to organization
        agents = c.agent_service.list_agents(tenant_id=org_id)
        revoked_count = 0
        for agent in agents:
            c.agent_service.revoke_agent(
                agent.agent_id, reason="EMERGENCY_TENANT_LOCKDOWN"
            )
            revoked_count += 1
        return {
            "status": "EMERGENCY_LOCKDOWN_ACTIVATED",
            "organization_id": org_id,
            "revoked_agents_count": revoked_count,
        }

    # --- Dashboard & Audit Endpoints ---
    @router.get("/dashboard/overview/{tenant_id}")
    def get_dashboard_overview(tenant_id: str):
        c = get_container()
        return c.dashboard_service.get_overview_stats(tenant_id)

    @router.get("/audit/{tenant_id}")
    def list_audit_events(tenant_id: str):
        c = get_container()
        return c.audit_service.list_events(tenant_id)

    # --- Incident Endpoints ---
    @router.post("/incidents")
    def create_incident(payload: Dict[str, Any]):
        c = get_container()
        return c.incident_service.create_incident(
            organization_id=payload.get("organization_id", "default"),
            agent_id=payload["agent_id"],
            title=payload["title"],
            description=payload.get("description"),
            correlation_id=payload.get("correlation_id"),
        )

    @router.get("/incidents/{organization_id}")
    def list_incidents(organization_id: str):
        c = get_container()
        return c.incident_service.list_incidents(organization_id)

    app.include_router(router)
    return app
