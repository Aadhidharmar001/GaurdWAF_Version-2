"""
Phase 8 Public Beta Launch Automated Test Suite.
Verifies Launch Checklist integrity, Beta Feedback Categories, Product Intelligence stream separation, Real-World Integrations, and Beta Dashboard execution.
"""

import os
import subprocess
import sys

from guardwaf.telemetry.product_telemetry import PRODUCT_INTELLIGENCE


def test_launch_checklist_document_exists():
    checklist_path = os.path.join("docs", "public_beta_launch_checklist.md")
    assert os.path.exists(checklist_path)


def test_beta_feedback_template_categories():
    template_path = os.path.join("docs", "beta_feedback_template.md")
    assert os.path.exists(template_path)
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "INSTALLATION_FAILURE" in content
    assert "FRAMEWORK_INTEGRATION_FAILURE" in content
    assert "MCP_COMPATIBILITY_ISSUE" in content


def test_product_intelligence_evidence_stream_separation():
    eng = PRODUCT_INTELLIGENCE.get_engineering_evidence()
    assert eng["automated_tests_passing"] >= 120
    assert eng["package_build_status"] == "PASS"

    ext = PRODUCT_INTELLIGENCE.get_external_developer_evidence()
    assert ext["external_developers_count"] == "UNKNOWN"
    assert ext["external_successful_integrations"] == "NOT YET MEASURED"


def test_beta_dashboard_script_execution():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "scripts/beta_dashboard.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "GUARdWAF PUBLIC BETA INTELLIGENCE" in res.stdout


def test_real_world_customer_support_agent_example():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [
        sys.executable,
        "examples/real_world_integrations/customer_support_agent/main.py",
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "REAL-WORLD CUSTOMER SUPPORT AGENT INTEGRATION COMPLETE" in res.stdout


def test_real_world_mcp_agent_example():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "examples/real_world_integrations/mcp_agent/main.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "REAL-WORLD MCP GATEWAY AGENT INTEGRATION COMPLETE" in res.stdout


def test_real_world_langgraph_workflow_example():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [
        sys.executable,
        "examples/real_world_integrations/langgraph_workflow/main.py",
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "REAL-WORLD LANGGRAPH WORKFLOW AGENT INTEGRATION COMPLETE" in res.stdout
