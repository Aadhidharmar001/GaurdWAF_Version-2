# 60-Second Quickstart Guide

Secure any Python AI agent tool function in less than 60 seconds.

---

## ⚡ Step 1 — Create Policy File (`policy.yaml`)

```yaml
metadata:
  policy_name: quickstart_policy
  version: "1.0.0"

rules:
  bulk_thresholds:
    - tool: issue_refund
      param_name: amount
      max_value: 100.0
```

---

## ⚡ Step 2 — Protect Tool in Code (`main.py`)

```python
from guardwaf import GuardWAF, protect, GuardWAFSecurityError

waf = GuardWAF(config_path="policy.yaml")


@protect(tool_name="issue_refund", client=waf)
def issue_refund(customer_id: str, amount: float):
    print(f"Refunding ${amount}")
    return {"status": "SUCCESS"}


with waf.session(session_id="sess_1"):
    # ALLOWED: $50.00
    issue_refund("cust_101", 50.0)

    # BLOCKED: $5,000.00
    try:
        issue_refund("cust_101", 5000.0)
    except GuardWAFSecurityError as err:
        print(f"🚨 BLOCKED: {err}")
```
