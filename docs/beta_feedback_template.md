# GuardWAF Public Beta Developer Feedback Template

Use this template to submit bug reports, integration friction, or developer experience feedback.

---

## 🏷️ Category Selection

Please select **one** primary category for your report:

- [ ] `INSTALLATION_FAILURE` — `pip install` or wheel build failed
- [ ] `DEPENDENCY_CONFLICT` — Package conflict with existing AI libraries
- [ ] `DOCUMENTATION_CONFUSION` — Unclear, missing, or misleading docs
- [ ] `POLICY_CONFUSION` — Difficulty setting up YAML/Pydantic rules
- [ ] `FRAMEWORK_INTEGRATION_FAILURE` — Error using LangChain, LangGraph, CrewAI, or Custom adapter
- [ ] `MCP_COMPATIBILITY_ISSUE` — Error using FastMCP or standard MCP gateway
- [ ] `PERFORMANCE_CONCERN` — Unexpected latency on local enforcement hot path
- [ ] `SECURITY_CONCERN` — Potential security bypass or invariant issue
- [ ] `FEATURE_REQUEST` — Suggested rule type or integration
- [ ] `GENERAL_FEEDBACK` — Overall developer experience thoughts

---

## 💻 Environment Information
- **GuardWAF Version**: e.g., `1.0.0`
- **Python Version**: e.g., `3.11.4`
- **OS & Environment**: e.g., `Ubuntu 22.04 LTS` / `macOS Sonoma` / `Windows 11`
- **Framework Used**: e.g., `LangChain v0.1.15` / `FastMCP` / `Custom Loop`

---

## 🔍 Feedback Details

### 1. Expected Behavior
What you expected GuardWAF to do.

### 2. Actual Behavior
What actually happened (include error messages or unexpected behavior).

### 3. Steps to Reproduce
Minimal code snippet demonstrating the issue.

```python
# Safe code snippet (REDACTED: Do not include secrets, API keys, or private customer data)
from guardwaf import GuardWAF, protect

# Your code here
```

> [!CAUTION]
> **Privacy Restriction**:
> **NEVER** include raw production API keys, database credentials, JWT tokens, private user prompts, or confidential customer payloads in your submission.
