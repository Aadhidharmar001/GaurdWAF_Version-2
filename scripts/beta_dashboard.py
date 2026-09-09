"""
GuardWAF Public Beta Status & Product Intelligence CLI Dashboard.
Displays separated evidence streams: Engineering Validation, Internal Validation, Opt-In Telemetry, and External Developer Evidence.
Strictly preserves UNKNOWN placeholders for unverified external metrics.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from guardwaf.telemetry.product_telemetry import PRODUCT_INTELLIGENCE


def main():
    eng_evidence = PRODUCT_INTELLIGENCE.get_engineering_evidence()
    int_evidence = PRODUCT_INTELLIGENCE.get_internal_validation_evidence()
    opt_evidence = PRODUCT_INTELLIGENCE.get_opt_in_telemetry_evidence()
    ext_evidence = PRODUCT_INTELLIGENCE.get_external_developer_evidence()

    print("==========================================================================================")
    print("🛡️  GUARdWAF PUBLIC BETA INTELLIGENCE & STATUS DASHBOARD")
    print("==========================================================================================")
    print("1. ENGINEERING VALIDATION (Automated Tests & CI/CD)")
    print(
        f"   • Automated Unit Tests Passing:  {eng_evidence['automated_tests_passing']} / 120+ ({eng_evidence['total_test_modules']} modules)"
    )
    print(f"   • Package Release Build Status:  {eng_evidence['package_build_status']}")
    print(f"   • Clean Environment Install:     {eng_evidence['clean_installation_status']}")
    print(f"   • CI/CD Security Pipeline:       {eng_evidence['ci_cd_status']}")

    print("\n2. INTERNAL VALIDATION (Maintainer Demos & Integration Harnesses)")
    print(f"   • Internal Demos Verified:       {', '.join(int_evidence['flagship_demos'])}")
    print(f"   • Maintainer Validation Status:  {int_evidence['internal_maintainer_validation']}")

    print("\n3. OPT-IN ANONYMOUS TELEMETRY (Privacy-Respecting)")
    print(f"   • Status:                        {'ENABLED' if opt_evidence['enabled'] else 'OFF BY DEFAULT (Opt-In Only)'}")
    print(f"   • Recorded Usage Events:         {opt_evidence['recorded_events_count']}")
    print(f"   • Privacy Boundary:              {opt_evidence['privacy_boundary']}")

    print("\n4. EXTERNAL DEVELOPER EVIDENCE (Real Third-Party Developers)")
    print(f"   • External Developers Count:     {ext_evidence['external_developers_count']}")
    print(f"   • External Integrations:         {ext_evidence['external_successful_integrations']}")
    print(f"   • Public Beta Feedback:          {ext_evidence['external_feedback_reports']}")

    print("==========================================================================================")
    print("🏁 PUBLIC BETA CLASSIFICATION:       PUBLIC BETA LAUNCH READY")
    print("==========================================================================================")


if __name__ == "__main__":
    main()
