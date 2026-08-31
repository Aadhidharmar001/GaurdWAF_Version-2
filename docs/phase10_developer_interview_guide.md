# GuardWAF Developer Interview Guide (20 Minutes)

This script guides qualitative 1-on-1 interviews with independent developers participating in Phase 10 beta validation.

---

## 🎯 Interview Principles
- **Neutrality**: Do NOT lead the participant toward positive answers.
- **Listen First**: Allow developers to express real security concerns in their own words.
- **Privacy Respect**: Never request confidential enterprise code, credentials, or customer payloads.

---

## 📋 Interview Question Script

### 1. Problem Discovery (4 Minutes)
- *How do you currently secure AI agent tool execution in your applications?*
- *What happens when your agent attempts an unauthorized or dangerous side effect?*
- *Where do your existing prompt-level guardrails stop working?*

### 2. Product Understanding (4 Minutes)
- *Based on GuardWAF's landing page or documentation, what problem do you think GuardWAF solves?*
- *What would you expect GuardWAF NOT to solve?*
- *Was the concept of in-process action authorization clear immediately?*

### 3. Integration & Setup (4 Minutes)
- *How straightforward was installing `guardwaf` and running the quickstart?*
- *Where did you experience friction or confusion during tool decoration (`@protect`) or policy setup?*
- *Which framework adapter did you use (LangChain, LangGraph, CrewAI, FastMCP, Custom)?*

### 4. Security & Trust Model (4 Minutes)
- *Did you understand the local enforcement model and parameter digest matching?*
- *Did you find the Human-in-the-Loop (HITL) suspension and resume workflow intuitive?*
- *Do you trust GuardWAF's fail-closed security guarantees?*

### 5. Value & Adoption Readiness (4 Minutes)
- *Would you deploy GuardWAF in your production agent workloads today?* (`[ ] Yes`, `[ ] Maybe`, `[ ] No`)
- *Why or why not? What is the primary barrier stopping you from adopting GuardWAF?*
- *What single feature or change would make GuardWAF significantly more valuable for your team?*
