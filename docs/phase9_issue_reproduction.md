# GuardWAF Beta Issue Reproduction & Sanitization Workflow

This document outlines the procedure for receiving, sanitizing, reproducing, and fixing developer issues reported during public beta.

---

## 🔄 Issue Reproduction Workflow

```text
External Developer Report Received
        │
        ▼
Privacy & Sanitization Review (Verify zero prompts/secrets attached)
        │
        ▼
Create Minimal Reproducible Code Example (tests/repro_issue_XXX.py)
        │
        ▼
Internal Maintainer Reproduction & Debugging
        │
        ▼
Severity & Priority Assessment (P0 - P4)
        │
        ▼
Root Cause Analysis & Code Edit
        │
        ▼
Automated Pytest Regression Test Creation
        │
        ▼
Patch Release & Beta Update
```

---

## 🔒 Code Sanitization Guidance for Developers
- **Secrets**: Replace real API keys or database passwords with `"redacted_dev_secret_key"`.
- **Prompts**: Replace customer prompts with generic placeholder text (`"User prompt placeholder"`).
- **Payloads**: Replace sensitive enterprise data with synthetic test dictionaries (`{"id": "test_101"}`).
