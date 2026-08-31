# GuardWAF Threat Model, Guarantees & Non-Guarantees

## 1. What GuardWAF Guarantees

* **Pre-Execution Deterministic Policy Enforcement**: In all supported integration paths (`@protect`, MCP Gateway, LangChain/CrewAI adapters), blocked actions return `status="blocked"` and result in **exactly ZERO downstream function body invocations**.
* **Cryptographic Parameter Binding**: HITL approval tokens are bound to SHA-256 parameter digests. Approvers cannot alter parameters during review.
* **Replay Protection**: Approved actions are tracked as `EXECUTED` in state stores. Duplicate resume attempts are rejected cleanly.
* **Tenant & Identity Isolation**: Identity context and tenant authorization boundaries are strictly verified server-side. Cross-tenant access fails fast.
* **Fault Isolation**: Telemetry, Control Plane outages, and event streaming failures NEVER affect or delay local runtime authorization ($O(1)$ hot path $< 1\text{ ms}$).

---

## 2. What GuardWAF Does NOT Guarantee (System Boundaries)

* **Internal Process Memory Attacks**: GuardWAF cannot prevent malicious code running with root/unrestricted access inside the same Python process from mutating internal memory directly.
* **External Side-Effect Idempotency**: GuardWAF guarantees atomic control over its authorization state. If a process crashes after downstream tool execution starts but before completion reporting, downstream idempotency keys are required to prevent duplicate external side-effects.
* **Unconfigured Identity Trust**: GuardWAF identity verification relies on trusted public key sets (JWKS) or shared secrets configured by system administrators.

---

## 3. Threat Matrix

| Threat | Mitigated By | Status |
| :--- | :--- | :--- |
| **Prompt Injection Tool Calls** | Pre-execution parameter digests, rate limits, sequence rules | ✅ PROTECTED |
| **Cross-Tenant Data Leakage** | Server-side tenant isolation checks & parameter scope rules | ✅ PROTECTED |
| **HITL Approval Token Replay** | Single-use idempotency tokens & state store tracking | ✅ PROTECTED |
| **Parameter Tampering During Review**| SHA-256 parameter digest verification in approval token | ✅ PROTECTED |
| **Stale Revocation Replay** | Monotonic sequence validation & signed revocation events | ✅ PROTECTED |
| **Control Plane Outage** | Local Last Known Good (LKG) policy fallback & SLA expiry | ✅ PROTECTED |
