# GuardWAF 60-Second Quickstart

This directory contains the simplest possible GuardWAF quickstart demonstration.

---

## ⚡ How to Run

```bash
# 1. Install GuardWAF
pip install guardwaf

# 2. Run Quickstart Script
python main.py
```

---

## 🔍 Code Explanation

```python
from guardwaf import GuardWAF, protect

# 1. Load policy from YAML file
waf = GuardWAF(config_path="policy.yaml")

# 2. Protect existing tool body
@protect(tool_name="issue_refund", client=waf)
def issue_refund(customer_id: str, amount: float):
    return {"status": "SUCCESS", "amount": amount}

# 3. Safe calls execute normally
issue_refund("cust_101", 50.0)

# 4. Dangerous calls are intercepted before function body executes
issue_refund("cust_101", 50000.0) # Triggers GuardWAFSecurityError!
```
