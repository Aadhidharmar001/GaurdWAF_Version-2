# GuardWAF Developer Quickstart Guide

Get up and running with **GuardWAF** in under 5 minutes to govern AI agent tool calls.

---

## 1. Installation

Install GuardWAF via `pip`:

```bash
pip install guardwaf
# Optional framework extras
pip install "guardwaf[langchain,mcp,redis]"
```

---

## 2. Basic Protected Tool Setup

Wrap your AI agent tools using the `@protect` decorator:

```python
from guardwaf import GuardWAF, protect, session, GuardWAFSecurityError, GuardWAFHITLRequiredError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule, HITLRule

# 1. Define Declarative Security Policy Rules
rules = PolicyRules(
    bulk_thresholds=[BulkThresholdRule(tool="process_refund", param_name="amount", max_value=5000)],
    hitl_rules=[HITLRule(tool="process_refund", condition_param="amount", greater_than=100.0)]
)
policy = PolicyConfig(metadata={"policy_name": "refund_policy"}, rules=rules)

# 2. Initialize GuardWAF Engine
waf = GuardWAF(policy=policy, secret_key="your_production_secret_key")

# 3. Protect Agent Tool Body
@protect(tool_name="process_refund")
def process_refund(customer_id: str, amount: float):
    return {"status": "SUCCESS", "refunded": amount}

waf.register_tool("process_refund", process_refund)
```

---

## 3. Running Tools in Session Context

Execute tools inside a `waf.session(...)` block:

```python
# Allowed Execution ($50 refund)
with waf.session(session_id="sess_101", tenant_id="org_acme"):
    result = process_refund("cust_101", 50.00)
    print("Allowed Result:", result)

# High-Risk Execution ($500 refund) -> Triggers HITL
with waf.session(session_id="sess_101", tenant_id="org_acme"):
    try:
        process_refund("cust_101", 500.00)
    except GuardWAFHITLRequiredError as e:
        print("Action suspended for Human-in-the-Loop approval!")
        print("PendingAction ID:", e.pending_action_id)
```

---

## 4. Resuming Approved Actions

When a Human Approver approves the pending action via the Control Plane, resume execution safely:

```python
with waf.session(session_id="sess_101", tenant_id="org_acme"):
    resumed_result = waf.resume_sync(
        pending_action_id=pending_action_id,
        approval_token=approval_token
    )
    print("Resumed Action Execution Result:", resumed_result)
```
