# GuardWAF External Developer Starter Kit

Welcome to the **GuardWAF Developer Beta**. This starter project demonstrates how to intercept, govern, and protect AI agent tool calls in under 60 seconds.

---

## 🎯 What This Demonstrates

In this minimal script (`main.py`):
1. **Allowed Action ($25.00)**: Complies with policy thresholds and executes the downstream tool.
2. **Blocked Action ($500.00)**: Exceeds the policy limit of $100.00. GuardWAF intercepts the call before execution, guaranteeing **zero downstream execution**.
3. **Human-in-the-Loop Action ($75.00)**: Triggers an approval gate and issues a cryptographically signed pending action token.

---

## 🚀 3-Step Quickstart

### Step 1: Clone the Repository & Enter Directory
```bash
git clone https://github.com/Aadhidharmar001/GaurdWAF_Version-2.git
cd GaurdWAF_Version-2/examples/external_beta
```

### Step 2: Create a Clean Virtual Environment & Install GuardWAF
```bash
# Create virtual environment
python -m venv .venv

# Activate it:
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install GuardWAF
pip install -e ../..
```

*(Alternatively, install directly from GitHub without cloning: `pip install "git+https://github.com/Aadhidharmar001/GaurdWAF_Version-2.git"`)*

### Step 3: Run the Starter Project
```bash
python main.py
```

---

## 📄 What You'll See

```text
================================================================================
🛡️  GUARDWAF EXTERNAL BETA STARTER PROJECT
================================================================================

▶ 1. Sending $25.00 Payment (Allowed by Policy)...
   ✅ ALLOWED: {'status': 'PAID', 'recipient': 'alice@example.com', 'amount': 25.0}
   Downstream Execution Count: 1

▶ 2. Sending $500.00 Payment (Exceeds Policy Maximum of $100.00)...
   🚨 BLOCKED ACTION INTERCEPTED: Action 'send_payment' blocked by GuardWAF policy: Bulk Threshold Exceeded: Parameter 'amount' value 500.0 exceeds max 100
   Downstream Execution Count: 1 (UNCHANGED)
   🔒 GUARANTEE CONFIRMED: Downstream tool was NEVER entered on blocked call.

▶ 3. Sending $75.00 Payment (Requires Human-in-the-Loop Approval)...
   ⏸️  HITL SUSPENDED: Action ID 'pa_...' requires HMAC approval.
   Downstream Execution Count: 1 (UNCHANGED)

================================================================================
✅ ALL TESTS PASSED! GuardWAF successfully protected your AI agent tools.
   Total Downstream Executions: 1 (Only the single allowed action ran)
================================================================================
```

---

## 🛠️ Files in this Kit

- `main.py`: Executable Python starter script with `@protect` decorator and execution counter.
- `policy.yaml`: Declarative YAML security policy configuring bulk threshold and HITL rules.

---

## 💬 Share Your Beta Feedback

Found a bug, have an integration request, or have questions?
- Submit feedback using our [GitHub Beta Feedback Form](../../.github/ISSUE_TEMPLATE/beta_feedback.yml).
- Review our [Public Beta Program Guide](../../docs/PUBLIC_BETA.md).
