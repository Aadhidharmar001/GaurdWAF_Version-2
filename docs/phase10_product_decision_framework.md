# GuardWAF Product Decision Engine Framework

This document specifies the evidence-based decision model governing feature roadmap prioritization and engineering investments.

---

## ⚖️ Prioritization Scoring Formula

Prioritization decisions are calculated using the 5-factor product formula:

$$\text{Decision Score} = \text{Developer Frequency} \times \text{Problem Severity} \times \text{Security Importance} \times \text{Developer Impact} \times \text{Reproducibility}$$

Where:
- **`Developer Frequency`** ($1 - 5$): Number of independent beta developers reporting the issue/need.
- **`Problem Severity`** ($1 - 5$): Technical impact on agent execution ($1 = \text{UI papercut}, 5 = \text{agent crash}$).
- **`Security Importance`** ($1 - 5$): Impact on GuardWAF security invariants ($1 = \text{dx suggestion}, 5 = \text{pre-execution bypass}$).
- **`Developer Impact`** ($1 - 5$): Strategic adoption blocker ($1 = \text{niche request}, 5 = \text{production deployment blocker}$).
- **`Reproducibility`** ($1 - 5$): Ease of reproducing via sanitized test harness ($1 = \text{unreproducible}, 5 = \text{reproducible test}$).

---

## 🚦 Priority Tiers & Action Plan

- **`P0 — IMMEDIATE FIX`**: Security invariant violation or pre-execution bypass. **Fix Target: Immediate Patch Release**.
- **`P1 — HIGH PRIORITY`**: Major framework adapter crash or package installation blocker. **Fix Target: Next Minor Sprint**.
- **`P2 — IMPORTANT`**: High boilerplate friction or policy configuration confusion reported by $\ge 3$ developers. **Fix Target: Next Release**.
- **`P3 — PLANNED`**: Non-blocking DX improvement, diagnostic CLI messaging enhancement. **Backlog Prioritization**.
- **`P4 — BACKLOG`**: Niche feature request or low-impact adapter extension. **Future Roadmap Evaluation**.
