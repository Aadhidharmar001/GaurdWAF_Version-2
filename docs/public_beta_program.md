# GuardWAF Real Developer Public Beta Program Guide

Welcome to the **GuardWAF Public Beta Program**!

---

## 🎯 Strategic Beta Purpose

GuardWAF has completed its internal engineering, production-readiness, packaging, and developer experience benchmarks. The objective of Phase 8 is **not** to add speculative security features, but to gather **independent real-world developer evidence** answering:

> **Can AI developers who did not build GuardWAF successfully discover, install, understand, integrate, and use GuardWAF to govern real AI agent actions?**

> [!NOTE]
> **Honest Evidence Notice**:
> All Phase 7 developer metrics (such as sub-10 minute onboarding times) were generated via automated clean-environment simulation scripts (`tests/test_simulated_developer_onboarding.py`). They represent internal engineering targets, **not real external developer adoption statistics**. Real adoption statistics will only be reported as real developers provide feedback.

---

## 🚀 Beta Developer Journey

```text
Discover GuardWAF
        │
        ▼
Install Package (pip install guardwaf)
        │
        ▼
Run 60-Second Quickstart
        │
        ▼
Protect First AI Agent Tool (@protect)
        │
        ▼
Trigger Policy Block / HITL Approval
        │
        ▼
Try Framework Integration (LangChain / LangGraph / CrewAI / MCP)
        │
        ▼
Provide Real Developer Feedback
```

---

## 📋 Target Feedback Areas

1. **Installation & Dependencies**:
   - Operating system and Python version (3.9 - 3.13).
   - Were dependency conflicts encountered with existing AI libraries?
2. **Conceptual Clarity & Understanding**:
   - Was GuardWAF's core purpose clear?
   - Did you understand the distinction between local in-process SDK enforcement and the Control Plane?
3. **Framework Integrations**:
   - Were LangChain, LangGraph, CrewAI, FastMCP, or Custom Agent adapters intuitive?
4. **Friction & Pain Points**:
   - Where did integration stall or get confusing?
   - Which policy rules or HITL flows required too much boilerplate configuration?

---

## 💬 Submitting Feedback & Bug Reports
- Submit categorized reports using our [GitHub Issue Templates](https://github.com/aadhidharmar001/guardwaf/issues).
- Discuss integration ideas on [GitHub Discussions](https://github.com/aadhidharmar001/guardwaf/discussions).
- Email confidential security reports to `security@guardwaf.io`.
