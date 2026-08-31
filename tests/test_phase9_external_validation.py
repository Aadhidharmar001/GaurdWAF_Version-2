"""
Phase 9 External Validation Automated Test Suite.
Verifies feedback schema, privacy boundaries, feedback intake automation, evidence stream separation, product learning dashboard, and security invariants.
"""

import pytest
import os
import sys
import json
import subprocess
from guardwaf.telemetry.product_telemetry import PRODUCT_INTELLIGENCE
from scripts.import_beta_feedback import validate_feedback_privacy, import_feedback_file

def test_phase9_feedback_schema_exists():
    schema_path = os.path.join("docs", "phase9_external_feedback_schema.md")
    assert os.path.exists(schema_path)

def test_phase9_onboarding_program_exists():
    onboarding_path = os.path.join("docs", "phase9_beta_onboarding_program.md")
    assert os.path.exists(onboarding_path)

def test_phase9_evidence_stream_separation():
    eng = PRODUCT_INTELLIGENCE.get_engineering_evidence()
    assert eng["automated_tests_passing"] >= 120
    assert eng["package_build_status"] == "PASS"

    ext = PRODUCT_INTELLIGENCE.get_external_developer_evidence()
    assert ext["external_developers_count"] == "UNKNOWN"
    assert ext["external_successful_integrations"] == "NOT YET MEASURED"

def test_feedback_privacy_validation_detector():
    clean_text = "Good package, loved the quickstart!"
    assert validate_feedback_privacy(clean_text) is True

    secret_text = "Here is my key: sk-proj-12345678901234567890"
    assert validate_feedback_privacy(secret_text) is False

def test_import_sample_beta_feedback():
    sample_path = os.path.join("data", "beta_feedback", "sample_feedback.json")
    assert os.path.exists(sample_path)
    fb = import_feedback_file(sample_path)
    assert fb["feedback_id"] == "fb_sample_2026_001"
    assert fb["installation_success"] is True

def test_product_learning_dashboard_script_execution():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "scripts/product_learning_dashboard.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "PRODUCT-MARKET LEARNING DASHBOARD" in res.stdout
    assert "INSUFFICIENT EXTERNAL EVIDENCE" in res.stdout

def test_import_beta_feedback_script_execution():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "scripts/import_beta_feedback.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "INTAKE COMPLETE" in res.stdout
