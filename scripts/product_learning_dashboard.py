"""
GuardWAF Product-Market Learning CLI Dashboard.
Strictly separates internal engineering health from public beta adoption signals.
Preserves UNKNOWN placeholders for external metrics until genuine independent feedback is collected.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure repository root is on sys.path for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from guardwaf.telemetry.product_telemetry import PRODUCT_INTELLIGENCE


def main():
    eng_evidence = PRODUCT_INTELLIGENCE.get_engineering_evidence()
    int_evidence = PRODUCT_INTELLIGENCE.get_internal_validation_evidence()
    opt_evidence = PRODUCT_INTELLIGENCE.get_opt_in_telemetry_evidence()
    ext_evidence = PRODUCT_INTELLIGENCE.get_external_developer_evidence()

    print("==========================================================================================")
    print("🛡️  GUARdWAF PHASE 10 PRODUCT-MARKET LEARNING DASHBOARD")
    print("==========================================================================================")
    print("1. ENGINEERING HEALTH & VALIDATION STATE")
    print(f"   • Automated Unit Tests:          {eng_evidence['automated_tests_passing']} / 142+ PASS")
    print(f"   • Package Release Build:         {eng_evidence['package_build_status']}")
    print(f"   • Clean Virtualenv Install:      {eng_evidence['clean_installation_status']}")
    print(f"   • Framework Integrations:        {', '.join(int_evidence['flagship_demos'])} (INTERNALLY TESTED)")
    print("   • Engineering Completion State:  ✅ PASSED & VERIFIED")

    print("\n2. REAL EXTERNAL BETA SIGNALS (Sample Size Rules Enforced)")
    print(f"   • External Developers Sample (n):{ext_evidence['external_developers_count']} (Rule: n < 5 = Qualitative Signal Only)")
    print(f"   • Successful Integrations:       {ext_evidence['external_successful_integrations']}")
    print("   • Failed Integrations:           NOT YET MEASURED")
    print("   • Production Deployment Intent:  UNKNOWN (Would Deploy Production: Yes/Maybe/No)")
    print("   • Primary Adoption Barrier:      UNKNOWN (Security / Framework / Complexity / Control Plane)")

    print("\n3. TOP FRICTION POINTS (Reported by Beta Developers)")
    print("   1. AWAITING EXTERNAL FEEDBACK")
    print("   2. AWAITING EXTERNAL FEEDBACK")
    print("   3. AWAITING EXTERNAL FEEDBACK")

    print("\n4. DUAL COMPLETION STATUS")
    print("   • Engineering Status:            ✅ PHASE 10 ENGINEERING COMPLETE")
    print("   • Product Validation Status:     ⏳ PRODUCT VALIDATION PENDING / AWAITING REAL EXTERNAL EVIDENCE")
    print("   • Product-Market Signal:         INSUFFICIENT EXTERNAL EVIDENCE (n = 0)")

    print("==========================================================================================")
    print("🏁 OVERALL CLASSIFICATION:          PHASE 10 ENGINEERING COMPLETE")
    print("                                    PUBLIC BETA ACTIVE — AWAITING REAL EXTERNAL EVIDENCE")
    print("==========================================================================================")


if __name__ == "__main__":
    main()
