import json
import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db, init_db
from app.db.orm_models import AuditLog, HitlQueue, SequenceState
from app.models import ToolCallRequest, ToolCallResponse
from app.rules_engine.loader import load_policy_from_yaml, parse_policy_yaml
from app.proxy.interceptor import evaluate_tool_call_request
from app.proxy.sequence_guard import record_sequence_state
from app.audit.logger import log_audit_event
from app.hitl.routes import router as hitl_router
from app.hitl.queue_manager import create_hitl_request
from app.health.routes import router as health_router
from app.llm.agent_client import run_agent_prompt
from app.realtime.broker import stream_dashboard_events
from app.red_team.scenarios import get_scenario_list, RED_TEAM_SCENARIOS
from app.compliance.report_generator import generate_compliance_report

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Agent WAF & Action Guardrail Gateway (PS-5.1)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"status": "GuardWAF API Gateway Running", "docs": "/docs"}

app.include_router(hitl_router)
app.include_router(health_router)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/logs")
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    results = []
    for l in logs:
        results.append({
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "agent_id": l.agent_id,
            "session_id": l.session_id,
            "tool": l.tool,
            "parameters": json.loads(l.parameters),
            "evaluation_outcome": l.evaluation_outcome,
            "matched_rule": l.matched_rule,
            "status": l.status,
            "latency_ms": getattr(l, "latency_ms", 0.0) or 0.0
        })
    return results

@app.get("/stream/events")
async def stream_events():
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(stream_dashboard_events(), media_type="text/event-stream", headers=headers)

@app.post("/proxy/tool", response_model=ToolCallResponse)
def proxy_tool_call(req: ToolCallRequest, db: Session = Depends(get_db)):
    start_t = time.time()
    policy = load_policy_from_yaml(settings.RULES_PATH)
    eval_res = evaluate_tool_call_request(req, policy, db)

    status = eval_res.status
    outcome = eval_res.outcome
    matched_rule = eval_res.matched_rule
    latency_ms = round((time.time() - start_t) * 1000, 2)

    eval_details = {
        "outcome": outcome,
        "matched_rule": matched_rule,
        "risk_score": eval_res.risk_score,
        "risk_level": eval_res.risk_level,
        "entropy": eval_res.entropy,
        "owasp_code": eval_res.owasp_code,
        "risk_factors": eval_res.risk_factors,
        "latency_ms": latency_ms
    }

    if status == "allowed":
        record_sequence_state(req.session_id, req.tool, db)
        log_audit_event(db, req.agent_id, req.session_id, req.tool, req.parameters, outcome, matched_rule, "allowed", latency_ms=latency_ms)
        return ToolCallResponse(
            status="allowed",
            message="Action permitted by GuardWAF.",
            evaluation_details=eval_details,
            result={"success": True, "details": f"Execution of '{req.tool}' completed."}
        )
    elif status == "blocked":
        log_audit_event(db, req.agent_id, req.session_id, req.tool, req.parameters, outcome, matched_rule, "blocked", latency_ms=latency_ms)
        return ToolCallResponse(
            status="blocked",
            message=f"Action blocked by GuardWAF: {outcome}",
            evaluation_details=eval_details
        )
    elif status == "pending_hitl":
        hitl_entry = create_hitl_request(db, req.agent_id, req.session_id, req.tool, req.parameters, matched_rule=matched_rule)
        log_audit_event(db, req.agent_id, req.session_id, req.tool, req.parameters, f"Paused for HITL approval (ID: {hitl_entry.id})", matched_rule, "pending_hitl", latency_ms=latency_ms)
        eval_details["hitl_id"] = hitl_entry.id
        eval_details["fraud_score"] = hitl_entry.fraud_score
        eval_details["confidence_score"] = hitl_entry.confidence_score
        return ToolCallResponse(
            status="pending_hitl",
            message=f"Action paused for human-in-the-loop review (ID: {hitl_entry.id}).",
            evaluation_details=eval_details
        )
    elif status == "shadow_blocked":
        record_sequence_state(req.session_id, req.tool, db)
        log_audit_event(db, req.agent_id, req.session_id, req.tool, req.parameters, outcome, matched_rule, "shadow_blocked", latency_ms=latency_ms)
        eval_details["shadow_mode"] = True
        return ToolCallResponse(
            status="allowed",
            message="Action permitted by GuardWAF (Shadow Mode).",
            evaluation_details=eval_details,
            result={"success": True, "details": f"Execution of '{req.tool}' completed (Shadow Mode)."}
        )

# --- Red Teaming Endpoints ---
@app.get("/redteam/scenarios")
def list_redteam_scenarios():
    return get_scenario_list()

@app.post("/redteam/simulate/{scenario_id}")
def simulate_redteam_scenario(scenario_id: str, db: Session = Depends(get_db)):
    if scenario_id not in RED_TEAM_SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario_info = RED_TEAM_SCENARIOS[scenario_id]
    tool_req = scenario_info["request"]

    # Execute directly through proxy endpoint logic
    response = proxy_tool_call(tool_req, db)
    return {
        "scenario": scenario_info["name"],
        "category": scenario_info["category"],
        "owasp": scenario_info["owasp"],
        "result": response
    }

# --- Compliance & Governance Endpoints ---
@app.get("/compliance/report")
def get_compliance_report(db: Session = Depends(get_db)):
    return generate_compliance_report(db)

# --- Policy Testing & Dry-Run Endpoints ---
@app.post("/policy/validate")
def validate_policy_content(data: dict):
    yaml_content = data.get("yaml_content", "")
    try:
        policy = parse_policy_yaml(yaml_content)
        return {
            "valid": True,
            "message": "Policy YAML syntax & schema validation passed.",
            "policy_name": policy.metadata.policy_name,
            "version": policy.metadata.version,
            "rule_count": len(policy.rules.rate_limits) + len(policy.rules.sequences) + len(policy.rules.bulk_thresholds) + len(policy.rules.data_scope) + len(policy.rules.parameter_blocklist)
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

@app.post("/agent/run")
def trigger_agent_run(prompt_data: dict, db: Session = Depends(get_db)):
    prompt = prompt_data.get("user_prompt", "")
    agent_id = prompt_data.get("agent_id", "demo-agent-01")
    session_id = prompt_data.get("session_id", "demo-session-01")
    return run_agent_prompt(prompt, agent_id, session_id, db)

