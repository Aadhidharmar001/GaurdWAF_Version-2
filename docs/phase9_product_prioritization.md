# GuardWAF Evidence-Based Product Prioritization Framework

This framework governs how future features, adapter enhancements, and DX fixes are prioritized for development.

---

## ⚖️ Prioritization Scoring Formula

Prioritization decisions are driven by the quantitative formula:

$$\text{Prioritization Score} = \text{Developer Frequency} \times \text{Problem Severity} \times \text{Security Importance} \times \text{Product Impact}$$

Where:
- **`Developer Frequency`** ($1 - 5$): How many independent beta developers report this issue/need.
- **`Problem Severity`** ($1 - 5$): Impact on agent functionality ($1 = \text{minor UI friction}, 5 = \text{agent crash}$).
- **`Security Importance`** ($1 - 5$): Impact on GuardWAF security invariants ($1 = \text{dx suggestion}, 5 = \text{pre-execution bypass}$).
- **`Product Impact`** ($1 - 5$): Strategic alignment with framework expansion ($1 = \text{niche edge case}, 5 = \text{core adoption blocker}$).

---

## 🚦 Priority Tiers

- **`P0 — CRITICAL SECURITY FAILURE`**: Pre-execution authorization bypass or zero-execution failure. **Immediate Fix Required**.
- **`P1 — MAJOR INTEGRATION BLOCKER`**: Package installation failure or crash on core framework adapter. **Sprint Blocker**.
- **`P2 — FREQUENT DEVELOPER FRICTION`**: High boilerplate friction or documentation confusion reported by $\ge 3$ developers. **Target for Next Release**.
- **`P3 — PRODUCT IMPROVEMENT`**: Non-blocking DX polish or diagnostic CLI messaging enhancement. **Backlog Prioritization**.
- **`P4 — NICE-TO-HAVE / ENHANCEMENT`**: Niche rule type or secondary framework integration request. **Future Roadmap Evaluation**.
