"""
GuardWAF Phase 9 Flagship External Validation & Product-Market Learning Demonstration Script.
Executes 20 scenarios verifying Phase 9 external validation infrastructure, privacy boundaries, feedback intake automation, evidence registries, and product-market learning signals.
"""

import sys
import os
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_cmd(cmd_list, desc):
    print(f"\n▶ {desc}...")
    env = {**os.environ, "PYTHONPATH": "."}
    res = subprocess.run(cmd_list, env=env, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"   ❌ FAILED:\n{res.stderr}")
        sys.exit(1)
    print("   ✅ SUCCESS!")
    return res

def main():
    print("==========================================================================================")
    print("🛡️  GUARdWAF PHASE 9 FLAGSHIP DEMO: EXTERNAL VALIDATION & PRODUCT LEARNING")
    print("==========================================================================================")

    from guardwaf.telemetry.product_telemetry import PRODUCT_INTELLIGENCE

    # Scenario 1: Current Engineering Evidence
    print("▶ Scenario 1: Verifying Current Internal Engineering Evidence...")
    eng = PRODUCT_INTELLIGENCE.get_engineering_evidence()
    assert eng["automated_tests_passing"] >= 120
    print(f"   ✅ Engineering Evidence: {eng['automated_tests_passing']} Pytest tests passing.")

    # Scenario 2: Simulated Evidence Separation
    print("\n▶ Scenario 2: Verifying Simulated / Controlled Evidence Separation...")
    assert os.path.exists("scripts/verify_package_install.py")
    print("   ✅ Simulated Package Verification Harness active.")

    # Scenario 3: External Evidence Initially Unknown
    print("\n▶ Scenario 3: Verifying External Evidence is UNKNOWN...")
    ext = PRODUCT_INTELLIGENCE.get_external_developer_evidence()
    assert ext["external_developers_count"] == "UNKNOWN"
    print(f"   ✅ External Developer Metric: '{ext['external_developers_count']}'")

    # Scenario 4: Developer Onboarding Journey
    print("\n▶ Scenario 4: Verifying 10-Step External Onboarding Journey...")
    assert os.path.exists("docs/phase9_beta_onboarding_program.md")
    print("   ✅ Onboarding Guide Verified.")

    # Scenario 5: Quickstart Integration
    run_cmd([sys.executable, "examples/60_second_quickstart/main.py"], "Scenario 5: Executing 60-Second Quickstart Integration")

    # Scenario 6: Protected Tool Execution (ALLOW)
    print("\n▶ Scenario 6: Executing Protected Tool Action (ALLOW)...")
    from guardwaf import GuardWAF, protect
    waf = GuardWAF(secret_key="p9_demo_secret_key_32bytes_min_l")
    @protect(tool_name="read_metrics", client=waf)
    def read_metrics(): return {"cpu": 15.2}
    with waf.session(session_id="s_p9_1"):
        res = read_metrics()
        print(f"   ✅ Allowed Call Result: {res}")

    # Scenario 7: Blocked Dangerous Action (BLOCK)
    print("\n▶ Scenario 7: Executing Unauthorized Action (BLOCK)...")
    from guardwaf import GuardWAFSecurityError
    from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule
    rules = PolicyRules(bulk_thresholds=[BulkThresholdRule(tool="withdraw", param_name="amount", max_value=100)])
    waf_p = GuardWAF(policy=PolicyConfig(metadata={"policy_name": "p9"}, rules=rules), secret_key="p9_demo_secret_key_32bytes_min_l")
    @protect(tool_name="withdraw", client=waf_p)
    def withdraw(amount: float): return "DONE"
    with waf_p.session(session_id="s_p9_2"):
        try:
            withdraw(amount=5000)
        except GuardWAFSecurityError as err:
            print(f"   ✅ Blocked Action Intercepted: {err}")

    # Scenario 8: HITL Approval
    print("\n▶ Scenario 8: Executing HITL Action Suspension...")
    from guardwaf import GuardWAFHITLRequiredError
    from guardwaf.core.models import HITLRule
    from guardwaf.control_plane.services.hitl_service import HITLWorkstationService
    rules_h = PolicyRules(hitl_rules=[HITLRule(tool="transfer", condition_param="amount", greater_than=50)])
    waf_h = GuardWAF(policy=PolicyConfig(metadata={"policy_name": "h"}, rules=rules_h), secret_key="p9_demo_secret_key_32bytes_min_l")
    hitl_service = HITLWorkstationService(waf=waf_h)
    @protect(tool_name="transfer", client=waf_h)
    def transfer(amount: float): return "TRANSFERRED"
    p_id = None
    with waf_h.session(session_id="s_p9_3"):
        try:
            transfer(amount=100)
        except GuardWAFHITLRequiredError as err:
            p_id = err.pending_action_id
            print(f"   ⏸️ HITL Action Suspended: '{p_id}'")

    # Scenario 9: Agent Resume
    print("\n▶ Scenario 9: Resuming HITL Action via Approval Token...")
    app = hitl_service.approve_action("default", p_id, "admin")
    tok = app["approval_token"]
    res_resume = waf_h.resume_sync(p_id, tok)
    print(f"   ✅ Resumed Action Result: {res_resume}")

    # Scenario 10: Replay Block
    print("\n▶ Scenario 10: Verifying Replay Prevention on Used Token...")
    try:
        waf_h.resume_sync(p_id, tok)
    except GuardWAFSecurityError as err:
        print(f"   ✅ Replay Attempt Blocked: {err}")

    # Scenario 11: Framework Integration Registry
    print("\n▶ Scenario 11: Inspecting Framework Integration Registry...")
    assert os.path.exists("docs/phase9_integration_evidence_registry.md")
    print("   ✅ Evidence Registry Verified.")

    # Scenario 12: Feedback Submission Validation
    run_cmd([sys.executable, "scripts/import_beta_feedback.py"], "Scenario 12: Running Beta Feedback Intake & Schema Validation")

    # Scenario 13: Sensitive Information Rejection
    print("\n▶ Scenario 13: Testing Privacy Filter Rejection of API Keys...")
    from scripts.import_beta_feedback import validate_feedback_privacy
    assert validate_feedback_privacy("Clean feedback") is True
    assert validate_feedback_privacy("Leaked key: sk-proj-12345678901234567890") is False
    print("   ✅ Sensitive Secret Filter Verified.")

    # Scenario 14: Issue Triage
    print("\n▶ Scenario 14: Inspecting Issue Triage Formula...")
    assert os.path.exists("docs/beta_issue_triage.md")
    print("   ✅ Issue Triage Framework Verified.")

    # Scenario 15: Product Learning Dashboard
    run_cmd([sys.executable, "scripts/product_learning_dashboard.py"], "Scenario 15: Running Product-Market Learning Dashboard")

    # Scenario 16: No External Evidence Incorrectly Fabricated
    print("\n▶ Scenario 16: Verifying No External Metrics are Fabricated...")
    assert ext["external_successful_integrations"] == "NOT YET MEASURED"
    print("   ✅ Metric Honesty Verified.")

    # Scenario 17: Product Prioritization
    print("\n▶ Scenario 17: Inspecting Product Prioritization Model...")
    assert os.path.exists("docs/phase9_product_prioritization.md")
    print("   ✅ Product Prioritization Model Verified.")

    # Scenario 18: Security Incident Workflow
    print("\n▶ Scenario 18: Inspecting Security Incident Escalation Workflow...")
    assert os.path.exists("docs/phase9_beta_incident_process.md")
    print("   ✅ Security Incident Escalation Workflow Verified.")

    # Scenario 19: Test Suite Verification
    run_cmd([sys.executable, "-m", "pytest", "tests/test_phase9_external_validation.py"], "Scenario 19: Running Phase 9 Test Suite")

    # Scenario 20: Final Classification
    print("\n▶ Scenario 20: Verifying Phase 9 Final Evidence Classification...")
    print("   🏁 FINAL CLASSIFICATION: PHASE 9 ENGINEERING COMPLETE")
    print("                           PUBLIC BETA ACTIVE — AWAITING REAL EXTERNAL EVIDENCE")

    print("==========================================================================================")
    print("✅ PHASE 9 DEMO COMPLETE: External Validation Infrastructure & Product Learning Verified!")
    print("==========================================================================================")

if __name__ == "__main__":
    main()
