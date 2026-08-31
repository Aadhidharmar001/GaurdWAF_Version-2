# GuardWAF Real Adoption Metrics Definitions

This document specifies the mathematical formulas for tracking developer activation, value discovery, and framework retention.

---

## 📐 Mathematical Metric Definitions

### 1. Developer Activation Rate
$$\text{Activation Rate} = \frac{\text{Independent Developers Who Protect & Execute First Tool}}{\text{Developers Who Begin Onboarding}}$$
*(Current Status: `UNKNOWN`)*

### 2. Time to First Value Rate
$$\text{First Value Rate} = \frac{\text{Developers Who Observe a Policy Block or HITL Action}}{\text{Developers Who Begin Onboarding}}$$
*(Current Status: `UNKNOWN`)*

### 3. Framework Integration Success Rate
$$\text{Integration Success Rate} = \frac{\text{Successful External Integrations}}{\text{Attempted External Integrations}}$$
*(Current Status: `UNKNOWN`)*

### 4. Feedback Completion Rate
$$\text{Feedback Completion Rate} = \frac{\text{Completed Feedback Reports}}{\text{Developers Who Completed Integration}}$$
*(Current Status: `UNKNOWN`)*

### 5. Security Issue Rate
$$\text{Security Issue Rate} = \frac{\text{Security-Related Reports}}{\text{Total External Integrations}}$$
*(Current Status: `UNKNOWN`)*

---

## 📊 Sample-Size Discipline Thresholds
- **$n < 5$**: Qualitative signal only. Report exact count (e.g. *"4 of 5 participants preferred X; early signal, insufficient sample (n=5)"*). Never convert small samples to percentages!
- **$5 \le n < 10$**: Early directional signal.
- **$10 \le n < 30$**: Moderate evidence.
- **$n \ge 30$**: Stronger directional evidence.
