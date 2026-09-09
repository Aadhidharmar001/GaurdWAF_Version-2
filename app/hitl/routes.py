from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.hitl.queue_manager import get_pending_hitl_requests, process_hitl_decision
from app.models import HITLDecision

router = APIRouter(prefix="/hitl", tags=["Human in the Loop"])


@router.get("/pending")
@router.get("/queue")
def list_pending(db: Session = Depends(get_db)):
    return get_pending_hitl_requests(db)


@router.post("/decide/{request_id}")
def decide_request(request_id: int, decision: HITLDecision, db: Session = Depends(get_db)):
    if decision.decision not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approve' or 'reject'")
    res = process_hitl_decision(db, request_id, decision.decision, decision.reason)
    if not res:
        raise HTTPException(status_code=404, detail="HITL request not found")
    return {
        "status": "success",
        "message": f"HITL request {request_id} marked as {res.status}",
    }
