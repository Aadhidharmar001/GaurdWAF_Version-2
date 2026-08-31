# GuardWAF External Beta Security Incident Handling & Resiliency Policy

Security is central to GuardWAF's purpose as an **Agent Action Authorization & Runtime Governance Platform**.

---

## 🛡️ Resilience & Fail-Closed Architectural Boundaries

GuardWAF enforces strict resiliency boundaries to prevent silent fail-open security bypasses:

1. **Control Plane Outage**:
   - SDK continues authorization using valid **Last Known Good (LKG)** cached policy bundle when within freshness rules ($0.819\text{ ms}$ hot-path latency).
   - If LKG bundle is stale, corrupt, or missing required state $\rightarrow$ Default to **`STRICT` mode $\rightarrow$ `BLOCK`**.
2. **Redis Outage**:
   - SDK gracefully falls back to local in-process thread-safe state store (`MemoryStateStore`).
   - Zero silent authorization fail-open.
3. **Telemetry & Dashboard Outage**:
   - Telemetry and streaming events fail independently in background tasks.
   - Local runtime authorization decision remains 100% secure and uninterrupted.

---

## 🚨 Security Incident Escalation SLAs

- **`P0 — CRITICAL VULNERABILITY`**: Zero-Execution Guarantee bypass, pre-execution authorization flaw, unauthenticated tenant isolation breach, or HMAC token forgery. **Triage SLA: < 4 Hours. Containment & Patch: < 12 Hours**.
- **`P1 — URGENT SECURITY FIX`**: Parameter digest tampering bypass, local revocation kill switch failure, or credential disclosure. **Triage SLA: < 12 Hours. Patch: < 24 Hours**.
- **`P2 — SCHEDULED FIX`**: Local denial of service or unexpected runtime crash under edge condition. **Patch: Next Target Release**.
- **`P3 / P4 — MINOR / ENHANCEMENT`**: Diagnostic CLI output polish or non-security logic edge case. **Triage into Backlog**.
