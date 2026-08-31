# GuardWAF External Beta Safety & Security Incident Handling Process

This policy details the emergency triage, escalation, containment, and patch release procedures for security findings reported during public beta.

---

## 🚨 Security Incident Escalation Tiers

- **`P0 — CRITICAL SECURITY INCIDENT`**: Zero-Execution Guarantee bypass, pre-execution authorization flaw, unauthenticated tenant isolation breach, or HMAC token forgery.
  - **Action**: Immediate containment, pull affected PyPI release if necessary, implement patch $< 12\text{ hours}$.
- **`P1 — URGENT SECURITY FIX`**: Parameter digest tampering bypass, local revocation kill switch failure, or credential disclosure vulnerability.
  - **Action**: Dedicated patch branch, regression test creation, release patch $< 24\text{ hours}$.
- **`P2 — SCHEDULED SECURITY FIX`**: Local denial of service or unexpected runtime crash under edge condition.
  - **Action**: Target fix in next patch release.
- **`P3 / P4 — MINOR / ENHANCEMENT`**: Diagnostic message polish or non-security logic edge case.
  - **Action**: Triage into backlog.

---

## 🔒 Incident Response Workflow

```text
Security Report Received (security@guardwaf.io)
        │
        ▼
Triage & Severity Classification (< 4 Hours)
        │
        ▼
Private Fix & Regression Test Creation (tests/test_p0_security_fixes.py)
        │
        ▼
Patch Release (e.g. guardwaf v1.0.1)
        │
        ▼
Public Security Advisory Publication
```
