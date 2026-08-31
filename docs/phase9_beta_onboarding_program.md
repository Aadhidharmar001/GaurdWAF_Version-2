# GuardWAF Phase 9 — External Developer Beta Onboarding Program

This document details the 10-step onboarding journey for external developers testing GuardWAF in public beta.

---

## 🗺️ 10-Step External Developer Onboarding Journey

```text
1. Discover GuardWAF
        │
        ▼
2. Understand the Problem (Zero Execution & Governance)
        │
        ▼
3. Install Package (pip install guardwaf)
        │
        ▼
4. Run 60-Second Quickstart (examples/60_second_quickstart/main.py)
        │
        ▼
5. Protect First Tool (@protect)
        │
        ▼
6. Trigger Blocked Action (exceed policy threshold)
        │
        ▼
7. Add Custom Policy (YAML / Pydantic PolicyConfig)
        │
        ▼
8. Integrate Preferred Framework (LangChain / LangGraph / CrewAI / MCP)
        │
        ▼
9. Try Human-in-the-Loop (HITL) Approval Flow
        │
        ▼
10. Submit Feedback (GitHub Issue / Anonymized Schema)
```

---

## 📋 Stage Breakdown, Friction Analysis & Documentation Links

| Stage # | Stage Name | Expected Outcome | Potential Friction Points | Documentation Link |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Discover GuardWAF** | Developer finds repo via GitHub/PyPI | Unclear positioning vs LLM guardrails | [README.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/README.md) |
| **2** | **Understand Problem** | Developer grasps Action-level governance | Confusing prompt guardrails with tool protection | [docs/concepts/action_envelope.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/concepts/action_envelope.md) |
| **3** | **Install Package** | Clean `pip install guardwaf` | Dependency conflicts with torch/transformers | [docs/getting_started/installation.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/getting_started/installation.md) |
| **4** | **Run Quickstart** | Allowed & blocked call executed in $< 60\text{s}$ | Python version incompatibility ($< 3.9$) | [docs/getting_started/quickstart.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/getting_started/quickstart.md) |
| **5** | **Protect First Tool** | Applies `@protect` to custom function | Function signature wrapping issues | [docs/getting_started/quickstart.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/getting_started/quickstart.md) |
| **6** | **Trigger Block** | Catches `GuardWAFSecurityError` | Expecting HTTP exceptions instead of SDK errors | [docs/concepts/policies.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/concepts/policies.md) |
| **7** | **Custom Policy** | Configures bulk thresholds or blocklists | YAML syntax formatting errors | [docs/concepts/policies.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/concepts/policies.md) |
| **8** | **Framework Adapter** | Integrates LangChain/LangGraph/CrewAI/MCP | Adapter instantiation signature confusion | [docs/getting_started/compatibility.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/getting_started/compatibility.md) |
| **9** | **HITL Flow** | Suspends & resumes action via token | Understanding HMAC approval tokens | [docs/concepts/hitl.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/concepts/hitl.md) |
| **10**| **Submit Feedback** | Fills out anonymized feedback template | Reluctance to open public GitHub issues | [docs/beta_feedback_template.md](file:///e:/AI_projects/GaurdWAF-PRODUCT/docs/beta_feedback_template.md) |
