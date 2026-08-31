# GuardWAF External Developer Public Beta Program Guide

Welcome to the **GuardWAF Phase 10 Public Beta Program**!

---

## 🎯 Strategic Purpose & Independent Completion States

GuardWAF Phase 10 evaluates whether real external developers understand, successfully integrate, trust, and derive value from GuardWAF when governing AI agent actions.

> [!IMPORTANT]
> **Independent Completion States**:
> - **`ENGINEERING COMPLETION`**: Internal tooling, feedback schemas, issue repro CLI, dashboards, and test suites are built and verified.
> - **`EXTERNAL VALIDATION COMPLETION`**: Real independent developers have participated, completed validation protocols, and submitted feedback.
> - **Overall Status**: `PHASE 10 ENGINEERING COMPLETE — PRODUCT VALIDATION PENDING / AWAITING REAL EXTERNAL EVIDENCE`.

---

## 👥 Target Participant Profile
- **Role**: AI Engineers, Backend Engineers, Security Architects, Agent Developers.
- **Technical Background**: Building AI agents using Python, LangChain, LangGraph, CrewAI, Model Context Protocol (MCP), or custom loops.
- **Use Case**: Agents capable of performing side effects (e.g., database updates, payments, refunds, cloud deployments, email sending).

---

## 🚀 Starter Kit & Quick Onboarding

Developers can clone the clean starter project in [`examples/external_beta/`](file:///e:/AI_projects/GaurdWAF-PRODUCT/examples/external_beta/):

```bash
cd examples/external_beta
pip install guardwaf
python main.py
```

Target Onboarding Benchmark:
- **First Protected Tool**: $< 10\text{ minutes}$
- **First Policy Block**: $< 15\text{ minutes}$

---

## 🔒 Privacy & Safety Rules
- **No Secrets**: Never upload API keys, passwords, or JWT tokens.
- **No Prompts**: Never upload private user prompts or confidential agent conversations.
- **No Customer PII**: Never upload real customer database records.

---

## 🚪 How to Withdraw
Participants may withdraw at any time by notifying maintainers at `beta@guardwaf.io`. All submitted feedback will remain strictly anonymized.
