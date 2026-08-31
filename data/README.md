# GuardWAF Beta Feedback Storage Directory

This directory stores ingested public beta feedback files.

---

## 🔒 Privacy & Data Retention Rules
- **No Git Tracking**: Real developer feedback files (`*.json`) in this directory are excluded from Git via `.gitignore`.
- **Anonymized Only**: Only anonymized, sanitized feedback adhering to `docs/phase9_external_feedback_schema.md` is ingested.
- **Sample File**: `sample_feedback.json` is provided for validation and local CLI dashboard testing.
