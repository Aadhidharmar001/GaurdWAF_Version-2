# GuardWAF Developer Interview Guide (15–20 Minutes)

This script guides qualitative 1-on-1 interviews with developers testing GuardWAF in public beta.

---

## 🎯 Interview Principles
- **Neutrality**: Do NOT lead the developer toward positive answers.
- **Listen First**: Allow developers to explain their security pain points in their own words.
- **Privacy Respect**: Never ask for confidential enterprise code, credentials, or customer payloads.

---

## 📋 Interview Question Script

### 1. Problem Discovery (3 Minutes)
- *Have you built an AI agent that invokes external tools, APIs, or databases?*
- *What specific tools or side effects can your agent perform?*
- *What is the worst thing that could happen if your agent takes an unprompted or unauthorized action?*
- *Have you ever experienced an unsafe, unintended, or out-of-scope tool invocation in production or staging?*

### 2. Current Security Approach (3 Minutes)
- *How do you currently prevent unauthorized agent tool execution?*
- *Do you rely on system prompt instructions, application code checks, framework middleware, or human approval?*
- *What limitations or friction have you encountered with your current approach?*

### 3. GuardWAF Understanding (4 Minutes)
- *Based on our documentation or landing page, what is your understanding of what GuardWAF does?*
- *Was the core concept of Action-level authorization clear immediately?*
- *What part of the architecture was most confusing or counter-intuitive?*

### 4. Integration Experience (5 Minutes)
- *How long did it take to install `guardwaf` and protect your first tool?*
- *Where did you get stuck during setup or policy configuration?*
- *Which framework integration did you use (LangChain, LangGraph, CrewAI, FastMCP, Custom)?*
- *Did you try the Human-in-the-Loop (HITL) flow or parameter digest matching?*

### 5. Value & Adoption Readiness (5 Minutes)
- *Would you deploy GuardWAF in your production agent workloads today? Why or why not?*
- *What single missing feature or DX friction point is currently stopping you from adopting GuardWAF?*
- *On a scale of 1 to 10, how likely are you to recommend GuardWAF to another AI engineer?*
