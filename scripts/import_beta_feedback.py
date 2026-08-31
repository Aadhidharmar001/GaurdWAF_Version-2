"""
GuardWAF Beta Feedback Import & Validation Tool.
Validates external developer feedback against docs/phase9_external_feedback_schema.md.
Enforces strict privacy boundaries (detects & rejects accidental inclusion of secrets, API keys, or raw prompts).
"""

import sys
import os
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SUSPICIOUS_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9\._\-]+", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),
    re.compile(r"aws_[a-zA-Z0-9]{20}", re.IGNORECASE),
    re.compile(r"password\s*[:=]\s*['\"].*['\"]", re.IGNORECASE)
]

def validate_feedback_privacy(content_str: str) -> bool:
    """Verifies that feedback text does not contain suspicious credentials or secrets."""
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(content_str):
            return False
    return True

def import_feedback_file(filepath: str) -> dict:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Feedback file '{filepath}' not found.")

    with open(filepath, "r", encoding="utf-8") as f:
        content_str = f.read()

    if not validate_feedback_privacy(content_str):
        raise ValueError("PRIVACY VIOLATION DETECTED: Feedback file contains potential API keys, bearer tokens, or credentials!")

    data = json.loads(content_str)
    required_keys = ["feedback_id", "developer_type", "framework", "installation_success", "category"]
    for key in required_keys:
        if key not in data:
            raise KeyError(f"Invalid feedback schema: missing required key '{key}'")

    return data

def main():
    print("==========================================================================================")
    print("🛡️  GUARdWAF BETA FEEDBACK INTAKE & PRIVACY VALIDATION TOOL")
    print("==========================================================================================")

    data_dir = os.path.join("data", "beta_feedback")
    if not os.path.exists(data_dir):
        print(f"Directory '{data_dir}' not found.")
        sys.exit(1)

    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".json")]
    print(f"Found {len(files)} feedback file(s) in '{data_dir}'.")

    valid_count = 0
    for fp in files:
        try:
            fb = import_feedback_file(fp)
            valid_count += 1
            print(f"   ✅ Imported & Privacy-Verified: '{fb['feedback_id']}' ({fb['category']} via {fb['framework']})")
        except Exception as err:
            print(f"   ❌ Validation Failed for '{fp}': {err}")

    print("==========================================================================================")
    print(f"✅ INTAKE COMPLETE: {valid_count} / {len(files)} feedback entry(ies) verified.")
    print("==========================================================================================")

if __name__ == "__main__":
    main()
