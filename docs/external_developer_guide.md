# GuardWAF External Developer Integration Guide

Welcome to GuardWAF! This guide provides a complete, step-by-step walkthrough for integrating GuardWAF runtime action governance into your AI agent applications in under **15 minutes**.

---

## 🎯 What GuardWAF Provides

GuardWAF acts as a **runtime security firewall** for AI agents, intercepting tool invocations before side effects occur in real-world systems.

Key capabilities:
- **Pre-Execution Interception**: Block unauthorized tool calls before function execution.
- **Human-in-the-Loop (HITL) Workflow**: Suspend high-risk actions safely until approved by a security administrator.
- **Zero Latency Overhead**: Local in-process policy evaluation operates in $< 1\text{ ms}$.
- **Transport Neutral**: Works with LangChain, CrewAI, MCP Gateway Proxy, or Custom Python Agent tools.

---

## 🚀 5-Step Integration Walkthrough

### Step 1: Install Package
```bash
pip install guardwaf
# Optional extra integrations:
# pip install "guardwaf[langchain,mcp,redis,observability,all]"
```

### Step 2: Initialize Client & Policy
```python
from guardwaf import GuardWAF
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule, HITLRule

rules = PolicyRules(
    bulk_thresholds=[
        BulkThresholdRule(tool="process_payment", param_name="amount", max_value=500.0)
    ],
    hitl_rules=[
        HITLRule(tool="process_payment", condition_param="amount", greater_than=200.0)
    ],
)
policy = PolicyConfig(metadata={"policy_name": "my_app_policy"}, rules=rules)
waf = GuardWAF(policy=policy, secret_key="your_32_byte_secret_key_here")
```

### Step 3: Decorate Agent Tools
```python
from guardwaf import protect


@protect(tool_name="process_payment", client=waf)
def process_payment(customer_id: str, amount: float):
    # This code executes ONLY if GuardWAF authorizes the action
    return f"Payment of ${amount:.2f} processed for {customer_id}."
```

### Step 4: Execute Tool Calls within Session Context
```python
with waf.session(session_id="sess_user_101", tenant_id="my_org"):
    # 1. Allowed call ($50.00)
    res = process_payment("cust_001", 50.0)
    print(res)

    # 2. High-value call ($300.00) -> Triggers HITL Suspension
    # 3. Policy violation ($1000.00) -> Blocked automatically
```

### Step 5: Handle Security Exceptions
```python
from guardwaf import GuardWAFSecurityError, GuardWAFHITLRequiredError

try:
    process_payment("cust_001", 1000.0)
except GuardWAFHITLRequiredError as err:
    print(f"Action suspended for admin approval: Action ID '{err.pending_action_id}'")
except GuardWAFSecurityError as err:
    print(f"Action blocked by GuardWAF policy: {err}")
```
