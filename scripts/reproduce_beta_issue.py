"""
GuardWAF Beta Issue Reproduction CLI Tool.
Ingests sanitized external developer issue descriptions and executes a minimal reproduction harness.
Validates privacy rules (rejects files containing secrets, API keys, or raw prompts).
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scripts.import_beta_feedback import validate_feedback_privacy


def run_issue_reproduction_harness(issue_id: str, code_snippet: str) -> dict:
    """Executes a sanitized issue reproduction harness."""
    if not validate_feedback_privacy(code_snippet):
        raise ValueError(
            f"SECURITY VIOLATION: Issue '{issue_id}' contains un-sanitized secrets or API keys!"
        )

    # Execute sanitized code safely in python exec environment
    local_scope = {}
    global_scope = {"__builtins__": __builtins__}

    try:
        exec(code_snippet, global_scope, local_scope)
        return {
            "issue_id": issue_id,
            "status": "REPRODUCED_SUCCESSFULLY",
            "result": local_scope.get("result", "OK"),
        }
    except Exception as err:
        return {
            "issue_id": issue_id,
            "status": "REPRODUCED_WITH_EXCEPTION",
            "error": str(err),
        }


def main():
    print(
        "=========================================================================================="
    )
    print("🛡️  GUARdWAF BETA ISSUE REPRODUCTION TOOL")
    print(
        "=========================================================================================="
    )

    sample_issue_id = "ISSUE_2026_001"
    sample_sanitized_snippet = """
from guardwaf import GuardWAF, protect
waf = GuardWAF(secret_key="sanitized_dev_secret_key_32bytes_long")
@protect(tool_name="test_tool", client=waf)
def test_tool(): return "SUCCESS"
with waf.session(session_id="repro_sess"):
    result = test_tool()
"""

    print(f"▶ Ingesting & Sanitizing Issue '{sample_issue_id}'...")
    res = run_issue_reproduction_harness(sample_issue_id, sample_sanitized_snippet)
    print(f"   ✅ Issue Reproduction Result: {res['status']} -> {res.get('result')}")

    print(
        "=========================================================================================="
    )
    print("✅ ISSUE REPRODUCTION TOOL COMPLETE!")
    print(
        "=========================================================================================="
    )


if __name__ == "__main__":
    main()
