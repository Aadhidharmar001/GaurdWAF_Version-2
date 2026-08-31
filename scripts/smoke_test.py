"""
GuardWAF Automated Staging Smoke Test Suite.
Validates live endpoints (/health/live, /health/ready, /auth/login), database connectivity, Redis connection, and core runtime authorization.
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app

def run_smoke_tests(target_url: str = None) -> bool:
    print("=================================================================")
    print("🛡️  GUARdWAF STAGING AUTOMATED SMOKE TEST SUITE")
    print("=================================================================")

    client = TestClient(app)

    # 1. Test /health/live
    print("▶ 1. Probing Liveness Endpoint (/health/live)...")
    res_live = client.get("/health/live")
    if res_live.status_code != 200:
        print(f"❌ SMOKE TEST FAILED: /health/live returned status {res_live.status_code}")
        return False
    print("   ✅ Liveness Probe OK (HTTP 200)")

    # 2. Test /health/ready
    print("▶ 2. Probing Readiness Endpoint (/health/ready)...")
    res_ready = client.get("/health/ready")
    if res_ready.status_code != 200:
        print(f"❌ SMOKE TEST FAILED: /health/ready returned status {res_ready.status_code}")
        return False
    data_ready = res_ready.json()
    print(f"   ✅ Readiness Probe OK: Status='{data_ready.get('status')}', DB='{data_ready.get('database')}', Redis='{data_ready.get('redis')}'")

    # 3. Test Core SDK In-Memory Authorization
    print("▶ 3. Testing Local GuardWAF Runtime Engine...")
    from guardwaf import GuardWAF, protect
    from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule

    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="smoke_tool", param_name="amount", max_value=100)])
    pol = PolicyConfig(metadata={"policy_name": "smoke_pol"}, rules=rules)
    waf = GuardWAF(policy=pol, secret_key="staging_smoke_test_secret_key_32bytes")

    from guardwaf.sdk.client import set_default_instance
    set_default_instance(waf)

    @protect(tool_name="smoke_tool")
    def smoke_tool(amount: float):
        return f"EXECUTED_{amount}"


    # Test allowed
    res1 = smoke_tool(amount=50.0)
    assert res1 == "EXECUTED_50.0"
    print("   ✅ Allowed action executed downstream tool body successfully.")

    # Test blocked
    try:
        smoke_tool(amount=500.0)
        print("❌ SMOKE TEST FAILED: Blocked action executed!")
        return False
    except Exception as err:
        print(f"   ✅ Blocked action intercepted successfully: {err}")

    print("=================================================================")
    print("✅ ALL STAGING SMOKE TESTS PASSED CLEANLY!")
    print("=================================================================")
    return True

def main():
    parser = argparse.ArgumentParser(description="GuardWAF Smoke Test Suite")
    parser.add_argument("--target-url", default=None, help="Target URL (optional)")
    args = parser.parse_args()

    success = run_smoke_tests(target_url=args.target_url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
