# GuardWAF External Issue Reproduction & Sanitization Workflow

This document outlines the systematic process for ingesting, sanitizing, reproducing, and fixing external developer issues reported during public beta.

---

## 🔄 Issue Reproduction Workflow

```text
External Developer Report Received
        │
        ▼
Privacy & Sanitization Review (Verify zero credentials, secrets, or prompts attached)
        │
        ▼
Create Minimal Reproducible Test Harness (scripts/reproduce_beta_issue.py)
        │
        ▼
Internal Maintainer Reproduction & Debugging
        │
        ▼
Severity & Priority Assessment (P0 - P4)
        │
        ▼
Root Cause Fix Implementation
        │
        ▼
Automated Pytest Regression Test Creation (tests/test_p0_security_fixes.py)
        │
        ▼
Patch Release & Evidence Registry Update
```

---

## 🔒 Code Sanitization Rules
- **Secrets**: Replace real API keys or database passwords with `"redacted_dev_secret_key"`.
- **Prompts**: Replace customer prompts with generic placeholder text (`"User prompt placeholder"`).
- **Payloads**: Replace sensitive enterprise data with synthetic test dictionaries (`{"id": "test_101"}`).
