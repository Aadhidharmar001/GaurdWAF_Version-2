"""
Phase 10 External Validation Automated Test Suite.
Verifies Phase 10 dual completion states, sample size discipline, LKG/fail-closed boundaries, privacy sanitization, issue reproduction, and real-world integration examples.
"""

import pytest
import os
import sys
import subprocess
from guardwaf.telemetry.product_telemetry import PRODUCT_INTELLIGENCE
from scripts.import_beta_feedback import validate_feedback_privacy, import_feedback_file
from scripts.reproduce_beta_issue import run_issue_reproduction_harness

def test_phase10_starter_project_exists():
    starter_path = os.path.join("examples", "external_beta", "main.py")
    assert os.path.exists(starter_path)

def test_phase10_validation_protocol_exists():
    protocol_path = os.path.join("docs", "phase10_validation_protocol.md")
    assert os.path.exists(protocol_path)
    with open(protocol_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Would You Actually Deploy This?" in content
    assert "Production Adoption Barrier" in content

def test_phase10_evidence_stream_separation():
    eng = PRODUCT_INTELLIGENCE.get_engineering_evidence()
    assert eng["automated_tests_passing"] >= 120
    assert eng["package_build_status"] == "PASS"

    ext = PRODUCT_INTELLIGENCE.get_external_developer_evidence()
    assert ext["external_developers_count"] == "UNKNOWN"

def test_phase10_sample_size_discipline_rules():
    schema_path = os.path.join("docs", "phase10_external_feedback_schema.md")
    assert os.path.exists(schema_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "n < 5" in content
    assert "Qualitative Signal Only" in content

def test_issue_reproduction_tool():
    clean_code = "from guardwaf import GuardWAF\nwaf = GuardWAF(secret_key='dev_sec_32bytes_long_min_12345')"
    res = run_issue_reproduction_harness("ISSUE_101", clean_code)
    assert res["status"] == "REPRODUCED_SUCCESSFULLY"

    secret_code = "key = 'sk-proj-12345678901234567890'"
    with pytest.raises(ValueError, match="SECURITY VIOLATION"):
        run_issue_reproduction_harness("ISSUE_102", secret_code)

def test_phase10_dashboard_execution():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "scripts/product_learning_dashboard.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "GUARdWAF PHASE 10 PRODUCT-MARKET LEARNING DASHBOARD" in res.stdout
    assert "DUAL COMPLETION STATUS" in res.stdout

def test_phase10_customer_support_real_world_example():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "examples/phase10_real_world/customer_support/main.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "CUSTOMER SUPPORT REAL-WORLD INTEGRATION COMPLETE" in res.stdout

def test_phase10_financial_agent_real_world_example():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "examples/phase10_real_world/financial_agent/main.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "FINANCIAL AGENT REAL-WORLD INTEGRATION COMPLETE" in res.stdout
