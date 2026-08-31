"""
GuardWAF Automated Repository Secret Scanner.
Scans codebase and config files for hardcoded production secrets, API tokens, AWS keys, and private keys.
Fails CI build if any production secrets are detected.
"""

import os
import re
import sys
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# Patterns representing suspicious hardcoded credentials
SECRET_PATTERNS = [
    (re.compile(r'(?i)aws_access_key_id\s*=\s*["\']?(AKIA[0-9A-Z]{16})["\']?'), "AWS Access Key ID"),
    (re.compile(r'(?i)aws_secret_access_key\s*=\s*["\']?([0-9a-zA-Z/+]{40})["\']?'), "AWS Secret Access Key"),
    (re.compile(r'-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----'), "Private Key Header"),
    (re.compile(r'(?i)postgres://[^:]+:([^\s@]+)@'), "Postgres Connection Password"),
    (re.compile(r'(?i)redis://:[^\s@]+@'), "Redis Password"),
    (re.compile(r'gw_live_[0-9a-f]{32}'), "Plaintext GuardWAF Production API Credential"),
]

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}
EXCLUDED_FILES = {"scan_secrets.py", "test_p0_security_fixes.py"}

def scan_file(filepath: str) -> List[Tuple[int, str, str]]:
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, 1):
                for pattern, secret_type in SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append((idx, secret_type, line.strip()))
    except Exception:
        pass
    return findings

def main() -> int:
    print("=================================================================")
    print("🛡️  GUARdWAF AUTOMATED SECRET SCANNER")
    print("=================================================================")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    total_findings = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for fname in filenames:
            if fname in EXCLUDED_FILES or fname.endswith((".pyc", ".db", ".zip", ".png", ".jpg")):
                continue
            fpath = os.path.join(dirpath, fname)
            findings = scan_file(fpath)
            if findings:
                rel_path = os.path.relpath(fpath, root_dir)
                for line_num, secret_type, snippet in findings:
                    print(f"❌ CRITICAL SECRET DETECTED in [{rel_path}:L{line_num}]: {secret_type}")
                    total_findings += 1

    if total_findings > 0:
        print(f"\n❌ BUILD FAILED: {total_findings} secret finding(s) detected.")
        return 1

    print("✅ SECRET SCAN PASSED: Zero hardcoded secrets detected across repository.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
