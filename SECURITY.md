# GuardWAF Security & Responsible Disclosure Policy

GuardWAF is designed as security-critical infrastructure for AI agent tool execution and action authorization. We take vulnerabilities with the utmost seriousness and appreciate responsible disclosure from security researchers and the developer community.

---

## 🔒 Reporting a Security Vulnerability

> [!CAUTION]
> **DO NOT disclose vulnerabilities via public GitHub issues, discussions, or pull requests.**
> Public disclosure before an authorized patch creates immediate risk for systems relying on GuardWAF for runtime authorization.

To report a vulnerability responsibly:

1. **GitHub Private Security Advisory (Preferred & Direct)**:
   Submit an advisory report through GitHub's private reporting interface:
   👉 **[Submit Private Security Advisory](https://github.com/Aadhidharmar001/GaurdWAF_Version-2/security/advisories/new)**

2. **Required Report Details**:
   - Component affected (e.g., Core SDK, Policy Engine, HITL Tokens, Framework Adapters, Control Plane).
   - Detailed description of the vulnerability and attack vector.
   - Minimal reproduction code or proof of concept (PoC) demonstrating the bypass.
   - Sanitized logs showing unauthorized downstream action execution or token bypass.
   - Do NOT include live production secrets, real API keys, or private customer data.

---

## ⏱️ Response & Acknowledgement SLAs

| Milestone | Target SLA | Description |
| :--- | :--- | :--- |
| **Initial Acknowledgement** | **Within 48 hours** | Confirm receipt of report and assign triage handler |
| **Triage & Reproducibility** | **Within 5 business days** | Validate vulnerability and assess impact severity |
| **Remediation & Patch** | **Within 14 business days** | Develop, test, and package security fix |
| **Coordinated Disclosure** | **Agreed release date** | Publish patched release along with official CVE / GitHub Advisory |

---

## 🎯 Scope & Vulnerability Severity Classification

We prioritize reports affecting the core security invariants of GuardWAF:

### Critical Severity (P0)
- **Pre-execution bypass**: An action blocked by policy executes downstream tool code.
- **HMAC token forgery**: Forging approval signatures to authorize suspended actions without the secret key.
- **Nonce / Replay bypass**: Replaying an already-consumed HITL approval token.
- **Tenant isolation breach**: Cross-tenant policy tampering or data leakage.

### High Severity (P1)
- **Parameter digest tampering**: Altering approved parameters between HITL suspension and downstream execution without detection.
- **Emergency kill switch failure**: Revoked agent or session successfully executing subsequent tool calls.
- **Denial of service on local hot path**: Malicious payload causing unbounded CPU/memory consumption in policy evaluation.

### Medium / Low Severity (P2 / P3)
- Incomplete error message sanitization leaking internal schema structures.
- Ambiguous policy validation parsing without security bypass.

---

## 🛡️ Remediation & Patch Workflow

1. **Confidential Patching**: Fixes are developed in private forks and validated against the full test suite and secret scanner.
2. **Regression Testing**: Security regression tests are added to ensure the vulnerability cannot reoccur.
3. **Release & Advisory**: A patch version is released, and a GitHub Security Advisory is published crediting the researcher (if desired).
