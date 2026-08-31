# GuardWAF Product Hypothesis Evaluation Matrix

This document tracks empirical evaluation of the 5 core Phase 9 product hypotheses.

---

## 📊 Sample-Size Disclaimer & Rules
- **`n < 5`**: Qualitative signal only. Must NOT claim statistical validation.
- **`5 <= n < 10`**: Early directional signal.
- **`10 <= n < 30`**: Moderate evidence.
- **`n >= 30`**: Stronger directional evidence.

---

## 🧪 Product Hypotheses Tracking Matrix

| Hypothesis ID | Statement | Current Evidence Sample Size ($n$) | Current Status | Empirical Findings & Qualitative Notes |
| :--- | :--- | :---: | :---: | :--- |
| **H1 (Problem Perception)** | Developers perceive Action-level authorization as distinct from LLM conversational prompt guardrails. | $n=0$ | `UNKNOWN` / `INSUFFICIENT_DATA` | Awaiting real third-party developer participation. |
| **H2 (Security Comprehension)** | Developers can configure GuardWAF policy rules and HITL flows without security background. | $n=0$ | `UNKNOWN` / `INSUFFICIENT_DATA` | Awaiting real third-party developer participation. |
| **H3 (Framework Value)** | Adapter availability (LangChain, LangGraph, CrewAI, FastMCP) materially reduces integration friction. | $n=0$ | `UNKNOWN` / `INSUFFICIENT_DATA` | Awaiting real third-party developer participation. |
| **H4 (MCP Demand)** | Growth in Model Context Protocol (MCP) servers creates demand for independent tool authorization proxies. | $n=0$ | `UNKNOWN` / `INSUFFICIENT_DATA` | Awaiting real third-party developer participation. |
| **H5 (Declarative Preference)** | Developers prefer declarative YAML/Pydantic policy files over inline custom code checks. | $n=0$ | `UNKNOWN` / `INSUFFICIENT_DATA` | Awaiting real third-party developer participation. |

---

## 📌 Allowed Hypothesis Statuses
- **`UNKNOWN`**: No data collected yet.
- **`SUPPORTED`**: Confirmed by empirical evidence across sufficient sample size.
- **`PARTIALLY_SUPPORTED`**: Supported by qualitative feedback, but with caveats or friction.
- **`NOT_SUPPORTED`**: Refuted by developer feedback.
- **`INSUFFICIENT_DATA`**: Sample size $n < 5$.
