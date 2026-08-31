# Public Beta Security Monitoring & Incident Response Policy

Security is central to GuardWAF's purpose as an **Agent Action Authorization & Runtime Governance Platform**.

---

## 🛡️ Vulnerability Severity Classification

- **`CRITICAL`**: Violation of Zero-Execution Guarantee, pre-execution authorization bypass, unauthenticated tenant isolation breach, or HMAC token forgery. **Triage SLA: < 4 Hours**.
- **`HIGH`**: Parameter digest tampering flaw, local revocation bypass, or secret leakage vulnerability. **Triage SLA: < 12 Hours**.
- **`MEDIUM`**: Denial of service on local enforcement, unexpected crash, or state store corruption. **Triage SLA: < 24 Hours**.
- **`LOW`**: Diagnostic information disclosure or non-security logic inconsistency. **Triage SLA: < 72 Hours**.

---

## 🔄 Vulnerability Response Workflow

```text
Report Received (security@guardwaf.io)
        │
        ▼
Initial Triage & SLA Acknowledgment (< 24 Hours)
        │
        ▼
Safe Reproduction in Isolated Test Harness
        │
        ▼
Severity Assessment & Security Advisory Draft
        │
        ▼
Security Patch Implementation
        │
        ▼
Automated Regression Test Suite Verification
        │
        ▼
Release Security Patch & Public Advisory
```

---

## 🔒 Security Guarantee Invariants
1. **Zero Downstream Execution**: If an action is blocked, downstream execution count MUST equal 0.
2. **Fail-Closed Security**: Network or database outages MUST fail closed.
3. **Parameter Digest Integrity**: Parameter mutation between evaluation and execution MUST cause execution abort.
