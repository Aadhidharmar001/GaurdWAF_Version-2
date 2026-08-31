from sqlalchemy.orm import Session
from app.models import ToolCallRequest, PolicyConfig, RuleResult
from app.proxy.interceptor import evaluate_tool_call_request

class RuleEngineEvaluator:
    def __init__(self, policy: PolicyConfig):
        self.policy = policy

    def evaluate(self, request: ToolCallRequest, db: Session) -> RuleResult:
        return evaluate_tool_call_request(request, self.policy, db)
