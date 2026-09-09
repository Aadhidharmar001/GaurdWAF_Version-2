"""
GuardWAF Clean-Environment Package Installation & Integration Verifier.
Installs generated .whl wheel package into an isolated virtual environment and verifies core SDK execution, policy loading, and tool interception without development dependencies.
"""

import os
import shutil
import subprocess
import sys
import venv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("=================================================================")
    print("🛡️  GUARdWAF CLEAN ENVIRONMENT PACKAGE INSTALLATION VERIFIER")
    print("=================================================================")

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dist_dir = os.path.join(root_dir, "dist")

    if not os.path.exists(dist_dir):
        print("❌ FAILED: 'dist/' directory does not exist. Run scripts/build_release.py first.")
        sys.exit(1)

    wheels = [f for f in os.listdir(dist_dir) if f.endswith(".whl")]
    if not wheels:
        print("❌ FAILED: No .whl file found in 'dist/'.")
        sys.exit(1)

    target_wheel = os.path.join(dist_dir, wheels[0])
    temp_env_dir = os.path.join(root_dir, ".temp_test_venv")

    if os.path.exists(temp_env_dir):
        shutil.rmtree(temp_env_dir)

    print(f"▶ 1. Creating Isolated Virtual Environment in '{temp_env_dir}'...")
    venv.create(temp_env_dir, with_pip=True)

    venv_python = os.path.join(temp_env_dir, "Scripts", "python.exe") if os.name == "nt" else os.path.join(temp_env_dir, "bin", "python")

    print(f"▶ 2. Installing Wheel '{wheels[0]}' in Clean Environment...")
    res_inst = subprocess.run(
        [venv_python, "-m", "pip", "install", target_wheel],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if res_inst.returncode != 0:
        print(f"❌ WHEEL INSTALLATION FAILED:\n{res_inst.stderr}")
        shutil.rmtree(temp_env_dir, ignore_errors=True)
        sys.exit(1)
    print("   ✅ Wheel Installed Successfully!")

    print("▶ 3. Verifying Import & Basic Execution in Clean Environment...")
    test_code = """
from guardwaf import GuardWAF, protect, GuardWAFSecurityError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule

rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="test_tool", param_name="val", max_value=10)])
policy = PolicyConfig(metadata={"policy_name": "clean_pol"}, rules=rules)
waf = GuardWAF(policy=policy, secret_key="clean_env_test_secret_key_32bytes_long")

@protect(tool_name="test_tool", client=waf)
def test_tool(val: int):
    return val * 2

with waf.session(session_id="clean_sess"):
    assert test_tool(val=5) == 10
    try:
        test_tool(val=50)
        raise RuntimeError("Blocked action executed!")
    except GuardWAFSecurityError:
        pass

print("CLEAN_VERIFICATION_SUCCESS")
"""
    res_run = subprocess.run([venv_python, "-c", test_code], capture_output=True, text=True, encoding="utf-8")

    # Clean up temporary virtual environment
    shutil.rmtree(temp_env_dir, ignore_errors=True)

    if "CLEAN_VERIFICATION_SUCCESS" not in res_run.stdout:
        print(f"❌ VERIFICATION FAILED:\n{res_run.stderr}")
        sys.exit(1)

    print("   ✅ GuardWAF SDK imported and executed cleanly in fresh environment.")
    print("=================================================================")
    print("✅ PACKAGE INSTALLATION VERIFICATION PASSED PERFECTLY!")
    print("=================================================================")


if __name__ == "__main__":
    main()
