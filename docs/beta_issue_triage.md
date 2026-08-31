# GuardWAF Beta Issue Triage & Priority Framework

This document outlines the systematic triage and prioritization framework for public beta issues and developer feedback.

---

## 🏷️ Issue Classification Categories

Every beta report is categorized into one of 7 canonical classes:

1. **`SECURITY`**: Vulnerability, invariant bypass, parameter tampering, or tenant isolation issue (Highest Priority).
2. **`BUG`**: Functionality error, unexpected exception, or logic flaw in SDK/Control Plane.
3. **`DX_FRICTION`**: Integration friction, boilerplate complexity, or confusing API signature.
4. **`FRAMEWORK_BREAKING_CHANGE`**: Ecosystem update in LangChain/LangGraph/CrewAI/MCP breaking adapter contracts.
5. **`DOCUMENTATION_GAP`**: Missing, outdated, or misleading instructions.
6. **`PERFORMANCE`**: Latency regression on local enforcement hot path ($> 1.0\text{ ms}$).
7. **`FEATURE_REQUEST`**: Proposed rule type, policy syntax enhancement, or integration.

---

## ⚖️ Priority Model Formula

Issue priority is calculated using the weighted score formula:

$$\text{Priority Score} = \text{Frequency} \times \text{Impact} \times \text{Security Impact}$$

### Priority Levels

- **`P0 — CRITICAL SECURITY`**: Security invariant violation, pre-execution authorization bypass, or zero-execution failure. **Fix SLA: < 24 Hours**.
- **`P1 — MAJOR BREAKAGE`**: SDK/Control Plane crash, package installation failure, or framework adapter breakage. **Fix SLA: < 48 Hours**.
- **`P2 — SIGNIFICANT FRICTION`**: Documentation error, confusing configuration, or high boilerplate friction. **Fix SLA: Sprint Target**.
- **`P3 — MINOR IMPROVEMENT`**: Non-blocking DX improvement, diagnostic message polish. **Fix SLA: Backlog**.
- **`P4 — ENHANCEMENT`**: Long-term feature request or ecosystem expansion. **Fix SLA: Roadmap Evaluation**.
