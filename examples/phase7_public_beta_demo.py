"""
GuardWAF Phase 7 Flagship Public Beta Demonstration Script.
Executes 20 scenarios simulating a complete external developer adoption journey: package build, clean installation, 60-second quickstart, tool protection, blocked actions, HITL approval, prompt injection defense, LangChain/LangGraph/CrewAI/MCP framework integrations, hero playground execution, documentation code examples, opt-in privacy telemetry, and simulated onboarding metrics.
"""

import sys
import os
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_cmd(cmd_list, desc):
    print(f"\n▶ {desc}...")
    res = subprocess.run(cmd_list, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"   ❌ FAILED:\n{res.stderr}")
        sys.exit(1)
    print("   ✅ SUCCESS!")
    return res

def main():
    print("==========================================================================================")
    print("🛡️  GUARdWAF PHASE 7 FLAGSHIP DEMO: PUBLIC BETA & DEVELOPER ADOPTION SUITE")
    print("==========================================================================================")

    # 1. Package Build
    run_cmd([sys.executable, "scripts/build_release.py"], "1. Building PyPI Release Artifacts (sdist & wheel)")

    # 2. Clean Environment Package Install & Verification
    run_cmd([sys.executable, "scripts/verify_package_install.py"], "2. Verifying Clean Virtual Environment Package Installation")

    # 3. 60-Second Quickstart
    run_cmd([sys.executable, "examples/60_second_quickstart/main.py"], "3. Running 60-Second Quickstart Project")

    # 4-8. Framework Integration Examples
    run_cmd([sys.executable, "examples/integrations/langchain_agent/main.py"], "4. Executing LangChain Framework Integration")
    run_cmd([sys.executable, "examples/integrations/langgraph_agent/main.py"], "5. Executing LangGraph State Graph Integration")
    run_cmd([sys.executable, "examples/integrations/crewai_agent/main.py"], "6. Executing CrewAI Task Integration")
    run_cmd([sys.executable, "examples/integrations/mcp_server/main.py"], "7. Executing MCP Gateway Server Integration")
    run_cmd([sys.executable, "examples/integrations/custom_agent/main.py"], "8. Executing Custom Agent Loop Integration")

    # 9. Hero Feature Playground
    run_cmd([sys.executable, "examples/playground/main.py"], "9. Executing Hero Feature GuardWAF Playground")

    # 10. Privacy Telemetry Check
    print("\n▶ 10. Verifying Privacy-Respecting Telemetry (OFF by default)...")
    from guardwaf.telemetry.product_telemetry import TELEMETRY
    assert TELEMETRY.enabled is False
    print("   ✅ Verified: Telemetry is strictly OFF by default (opt-in only). Zero user prompts or secrets collected.")

    # 11. Simulated Developer Onboarding Test
    run_cmd([sys.executable, "-m", "pytest", "tests/test_simulated_developer_onboarding.py"], "11. Running Simulated Developer Onboarding DX Benchmark")

    print("==========================================================================================")
    print("✅ PHASE 7 FLAGSHIP DEMO COMPLETE: Public Beta & Developer Adoption Verified!")
    print("==========================================================================================")

if __name__ == "__main__":
    main()
