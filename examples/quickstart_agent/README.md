# GuardWAF External Developer Quickstart

Get started protecting your AI agent's actions in under **15 minutes**.

---

## 🚀 Quickstart Guide

### 1. Installation
```bash
pip install guardwaf
```

### 2. Basic Usage (`main.py`)
```python
from guardwaf import GuardWAF, protect
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule

# 1. Initialize GuardWAF Engine
rules = PolicyRules(
    bulk_thresholds=[BulkThresholdRule(tool="process_payment", param_name="amount", max_value=500.0)]
)
policy = PolicyConfig(metadata={"policy_name": "my_policy"}, rules=rules)
waf = GuardWAF(policy=policy, secret_key="your_32_byte_secret_key_here")

# 2. Decorate Tool Functions
@protect(tool_name="process_payment", client=waf)
def process_payment(customer_id: str, amount: float):
    return f"Payment of ${amount} processed."

# 3. Execute Actions in Session
with waf.session(session_id="sess_001"):
    process_payment("cust_123", 50.0)   # Allowed
    process_payment("cust_123", 1000.0) # Blocked by GuardWAF
```

### 3. Run Quickstart Demonstration
```bash
python main.py
```
