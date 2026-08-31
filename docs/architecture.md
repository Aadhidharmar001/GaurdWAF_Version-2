# GuardWAF System Architecture & Subsystem Specification

GuardWAF is an **Agent Action Authorization & Runtime Governance Platform** designed to intercept, authorize, suspend, or block autonomous AI agent tool calls before real-world side effects execute.

---

## Subsystem Architecture

```text
               ┌────────────────────────────────────────────────────────┐
               │                  GUARDWAF SDK CLIENT                   │
               │                                                        │
               │  @protect() Decorator / Framework Adapters             │
               │       │                                                │
               │       ▼                                                │
               │  ActionEnvelope (Transport Neutral)                    │
               │       │                                                │
               │       ▼                                                │
               │  O(1) Local Revocation Kill Switch                     │
               │       │                                                │
               │       ▼                                                │
               │  Identity & Delegated Authority Evaluator              │
               │       │                                                │
               │       ▼                                                │
               │  Declarative Rules & ML Risk Engine                    │
               │       │                                                │
               │       ├───────────────────────┬──────────────────┐     │
               │       ▼                       ▼                  ▼     │
               │   [ALLOWED]               [BLOCKED]       [REQUIRE HITL]
               │       │                       │                  │     │
               │       ▼                       ▼                  ▼     │
               │  Issue Grant           Abort Execution     Suspend Execution
               └───────┬──────────────────────────────────────────┬─────┘
                       │                                          │
                       ▼                                          ▼
            REAL DOWNSTREAM TOOL                         HITL WORKSTATION
             (DB, API, Payments)                         (Approval Engine)
```

---

## Core Security Invariants
1. **Zero Hot-Path Network Dependencies**: Policy evaluation and local revocation checks run in-process ($< 1\text{ ms}$) without Control Plane network calls.
2. **Fail-Closed Design**: Telemetry or network errors NEVER cause fail-open authorization.
3. **Cryptographic Integrity**: Action Grants, HITL approval tokens, parameter digests, policy bundles, and signed revocation events are signed using HMAC-SHA256 / Ed25519.
