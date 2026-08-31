# GuardWAF Phase 10 External Developer Validation Protocol

This document specifies the 8 standardized experiments that external developers are invited to perform during public beta testing.

---

## 🧪 Standardized Experiment Suite

```text
Experiment 1: Package Installation & Setup
        │
        ▼
Experiment 2: Protect First Python Tool (@protect)
        │
        ▼
Experiment 3: Policy Rule Configuration (YAML / Pydantic)
        │
        ▼
Experiment 4: Policy Block Verification
        │
        ▼
Experiment 5: Human-in-the-Loop (HITL) Workflow
        │
        ▼
Experiment 6: Framework Adapter Integration (LangChain / LangGraph / CrewAI / MCP)
        │
        ▼
Experiment 7: Production Boundary Understanding
        │
        ▼
Experiment 8: Production Adoption Barrier & Intent ("Would You Actually Deploy This?")
```

---

## 📋 Experiment Protocols & Verification Tasks

### Experiment 1 — Installation
- **Objective**: Verify whether developer can install `guardwaf` without assistance.
- **Task**: Execute `pip install guardwaf` in a fresh virtualenv.

### Experiment 2 — First Protected Tool
- **Objective**: Apply `@protect` decorator to a standard Python function.
- **Target Time**: $< 10\text{ minutes}$.

### Experiment 3 — Policy Configuration
- **Objective**: Modify `policy.yaml` to define custom bulk thresholds and blocklists.

### Experiment 4 — Policy Block Verification
- **Objective**: Intentionally trigger a policy violation and catch `GuardWAFSecurityError`.
- **Target Time**: $< 15\text{ minutes}$.

### Experiment 5 — HITL Workflow
- **Objective**: Trigger `GuardWAFHITLRequiredError`, inspect pending action ID, approve via workstation service, and call `waf.resume_sync()`.

### Experiment 6 — Framework Adapter Integration
- **Objective**: Wrap an agent tool using `LangChainAdapter`, `LangGraphAdapter`, `CrewAIAdapter`, or `MCPGatewayProxy`.

### Experiment 7 — Production Boundary Understanding
- **Objective**: Explain what GuardWAF protects (Action authorization & parameter digests) vs what it does NOT protect (LLM prompt sentiment).

### Experiment 8 — Production Adoption Barrier ("Would You Actually Deploy This?")
- **Objective**: Uncover actual production deployment blockers.
- **Question 1**: *Would you deploy GuardWAF in your production agent workloads?* (`[ ] Yes`, `[ ] Maybe`, `[ ] No`).
- **Question 2**: *What single missing capability or adoption barrier is currently stopping you from deploying GuardWAF?*
  - `[ ] Security concerns / Trust model`
  - `[ ] Missing framework adapter`
  - `[ ] Too difficult / verbose to configure`
  - `[ ] Absence of fully hosted Control Plane SaaS`
  - `[ ] Latency / Performance concerns`
  - `[ ] Don't understand problem / Value proposition`
  - `[ ] Already building custom in-house authorization`
