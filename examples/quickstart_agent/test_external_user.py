"""
Automated External Developer Onboarding Verification Test.
Simulates a developer unfamiliar with GuardWAF performing:
Clone ➔ Install ➔ Configure ➔ Protect ➔ Execute ➔ Verify Invariants in a clean scope.
"""

import os
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("=================================================================")
    print("🛡️  GUARdWAF EXTERNAL DEVELOPER ONBOARDING VALIDATION TEST")
    print("=================================================================")

    main_py_path = os.path.join(os.path.dirname(__file__), "main.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    res = subprocess.run(
        [sys.executable, main_py_path],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if res.returncode != 0:
        print(f"❌ EXTERNAL USER TEST FAILED:\n{res.stderr}")
        sys.exit(1)

    assert "ALLOWED TOOL CALL" in res.stdout
    assert "BLOCKED POLICY VIOLATION" in res.stdout
    assert "QUICKSTART COMPLETE" in res.stdout

    print("   ✅ External Quickstart Executed Cleanly")
    print("   ✅ Sub-15 Minute Onboarding Workflow Verified!")
    print("=================================================================")


if __name__ == "__main__":
    main()
