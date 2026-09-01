"""
Master In-Process Rule Evaluator.
Evaluates ActionIntent against PolicyConfig using pluggable StateStore.
Saves immutable PendingAction records for HITL workflow suspension.
"""

import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from guardwaf.core.canonical import canonicalize_parameters
from guardwaf.core.models import (
    ActionIntent,
    ActionState,
    PendingAction,
    PolicyConfig,
    RuleResult,
)
from guardwaf.hitl.tokens import HITLTokenManager
from guardwaf.state.base import StateStore
from guardwaf.state.memory import MemoryStateStore


class ActionEvaluator:
    def __init__(self, policy: PolicyConfig, state_store: Optional[StateStore] = None):
        self.policy = policy
        self.state_store = state_store or MemoryStateStore()
        self.hitl_token_mgr = HITLTokenManager()

    def evaluate(self, intent: ActionIntent) -> RuleResult:
        global_shadow = self.policy.shadow_mode
        rules = self.policy.rules
        session_id = (
            intent.session_context.session_id
            if intent.session_context
            else "default_session"
        )
        principal_id = (
            intent.session_context.principal_id if intent.session_context else None
        )

        # 1. Rate Limiting Check
        for rule in rules.rate_limits:
            if rule.tool == intent.tool_name:
                count = self.state_store.get_tool_call_count(
                    session_id, intent.tool_name, rule.window_seconds
                )
                if count >= rule.max_calls:
                    is_shadow = rule.shadow_mode or global_shadow
                    status = "shadow_blocked" if is_shadow else "blocked"
                    return RuleResult(
                        status=status,
                        outcome=f"Rate Limit Exceeded: Max {rule.max_calls} calls in {rule.window_seconds}s for tool '{intent.tool_name}' (Current: {count})",
                        matched_rule=f"rate_limits: max {rule.max_calls}/{rule.window_seconds}s",
                        risk_score=0.75,
                        risk_level="HIGH",
                    )

        # 2. Sequence Enforcement Check
        for rule in rules.sequences:
            if rule.tool == intent.tool_name:
                predecessors = rule.get_predecessors()
                for pred in predecessors:
                    if not self.state_store.has_executed_predecessor(session_id, pred):
                        is_shadow = rule.shadow_mode or global_shadow
                        status = "shadow_blocked" if is_shadow else "blocked"
                        return RuleResult(
                            status=status,
                            outcome=f"Sequence Violation: Tool '{intent.tool_name}' requires prior execution of '{pred}' in session '{session_id}'",
                            matched_rule=f"sequences: required '{pred}'",
                            risk_score=0.85,
                            risk_level="HIGH",
                        )

        # 3. Bulk Operations Threshold Check
        for rule in rules.bulk_thresholds:
            if rule.tool == intent.tool_name:
                val = intent.parameters.get(rule.param_name)
                if isinstance(val, (int, float)) and val > rule.max_value:
                    is_shadow = rule.shadow_mode or global_shadow
                    status = "shadow_blocked" if is_shadow else "blocked"
                    return RuleResult(
                        status=status,
                        outcome=f"Bulk Threshold Exceeded: Parameter '{rule.param_name}' value {val} exceeds max {rule.max_value}",
                        matched_rule=f"bulk_thresholds: max {rule.max_value} for '{rule.param_name}'",
                        risk_score=0.70,
                        risk_level="HIGH",
                    )

        # 4. Data Scope & Session Context Check
        for rule in rules.data_scope:
            if rule.tool == intent.tool_name:
                param_val = intent.parameters.get(rule.param_name)
                # Check session customer_id match
                if rule.check_session_customer_id or rule.param_name == "customer_id":
                    if intent.session_context and intent.session_context.customer_id:
                        session_cust_id = str(intent.session_context.customer_id)
                        target_cust_id = (
                            str(param_val) if param_val is not None else None
                        )
                        if target_cust_id != session_cust_id:
                            is_shadow = rule.shadow_mode or global_shadow
                            status = "shadow_blocked" if is_shadow else "blocked"
                            return RuleResult(
                                status=status,
                                outcome=f"Data Scope Mismatch: Session customer_id '{session_cust_id}' does not match requested data customer_id '{target_cust_id}'",
                                matched_rule=f"data_scope: session customer_id match required for '{rule.param_name}'",
                                risk_score=0.90,
                                risk_level="CRITICAL",
                            )

                # Check allowed scope IDs list
                if (
                    intent.session_context
                    and intent.session_context.allowed_scope_ids
                    and param_val is not None
                ):
                    allowed_scope_ids = {
                        str(sid) for sid in intent.session_context.allowed_scope_ids
                    }
                    if str(param_val) not in allowed_scope_ids:
                        is_shadow = rule.shadow_mode or global_shadow
                        status = "shadow_blocked" if is_shadow else "blocked"
                        return RuleResult(
                            status=status,
                            outcome=f"Declared Scope Violation: Parameter '{rule.param_name}' value '{param_val}' not in allowed scope {sorted(allowed_scope_ids)}",
                            matched_rule=f"data_scope: allowed_scope check for '{rule.param_name}'",
                            risk_score=0.85,
                            risk_level="HIGH",
                        )

        # 5. Parameter Blocklist Check
        for rule in rules.parameter_blocklist:
            if rule.tool == intent.tool_name:
                param_val = intent.parameters.get(rule.param_name)
                if param_val is not None:
                    val_str = str(param_val)
                    for pattern in rule.blocklist:
                        if re.search(pattern, val_str, re.IGNORECASE):
                            is_shadow = rule.shadow_mode or global_shadow
                            status = "shadow_blocked" if is_shadow else "blocked"
                            return RuleResult(
                                status=status,
                                outcome=f"Parameter Blocklist Trigger: Parameter '{rule.param_name}' matched blocked pattern '{pattern}'",
                                matched_rule=f"parameter_blocklist: matched '{pattern}' on '{rule.param_name}'",
                                risk_score=0.95,
                                risk_level="CRITICAL",
                            )

        # 6. HITL Rules Check
        for rule in rules.hitl_rules:
            if rule.tool == intent.tool_name:
                if rule.condition_param and rule.greater_than is not None:
                    val = intent.parameters.get(rule.condition_param)
                    if isinstance(val, (int, float)) and val > rule.greater_than:
                        pending_id = f"pa_{uuid.uuid4().hex[:12]}"
                        now = datetime.now(timezone.utc)
                        expires_at = now + timedelta(seconds=600)  # 10 min HITL TTL
                        canon_params = canonicalize_parameters(intent.parameters)
                        intent_digest = hashlib.sha256(
                            intent.model_dump_json().encode("utf-8")
                        ).hexdigest()

                        tok = self.hitl_token_mgr.generate_approval_token(
                            pending_action_id=pending_id,
                            action_intent_digest=intent_digest,
                            parameter_digest=intent.parameter_digest,
                            session_id=session_id,
                            agent_id=intent.agent_id,
                        )

                        tenant_id = (
                            intent.session_context.tenant_id
                            if (
                                intent.session_context
                                and intent.session_context.tenant_id
                            )
                            else "default"
                        )
                        pending_action = PendingAction(
                            pending_action_id=pending_id,
                            tenant_id=tenant_id,
                            agent_id=intent.agent_id,
                            delegating_principal=principal_id,
                            session_id=session_id,
                            tool_name=intent.tool_name,
                            canonical_parameters=canon_params,
                            parameters=intent.parameters,
                            parameter_digest=intent.parameter_digest,
                            action_intent_digest=intent_digest,
                            policy_decision="pending_hitl",
                            matched_rule=f"hitl_rules: '{rule.condition_param}' > {rule.greater_than}",
                            created_at=now,
                            expires_at=expires_at,
                            status=ActionState.PENDING,
                            idempotency_key=f"idemp_{uuid.uuid4().hex[:12]}",
                            approval_token=tok,
                        )

                        # Save durable pending action into state store
                        self.state_store.save_pending_action(pending_action)

                        is_shadow = rule.shadow_mode or global_shadow
                        status = "shadow_blocked" if is_shadow else "pending_hitl"
                        return RuleResult(
                            status=status,
                            outcome=f"HITL Approval Required: Parameter '{rule.condition_param}' ({val}) exceeds threshold {rule.greater_than}",
                            matched_rule=f"hitl_rules: '{rule.condition_param}' > {rule.greater_than}",
                            risk_score=0.60,
                            risk_level="MEDIUM",
                            hitl_id=pending_id,
                            hitl_approval_token=tok,
                            pending_action=pending_action,
                        )

        return RuleResult(
            status="allowed",
            outcome="Action Permitted by Policy.",
            matched_rule=None,
            risk_score=0.0,
            risk_level="LOW",
        )
