"""
Unit Tests for GuardWAF Developer CLI Commands.
"""

import os
import json
import pytest
from guardwaf.cli import run_doctor, runtime_status_cmd, validate_policy_cmd, verify_bundle_cmd

def test_cli_doctor():
    # Verify run_doctor completes without unhandled errors
    run_doctor()

def test_cli_runtime_status():
    runtime_status_cmd()

def test_cli_validate_policy(tmp_path):
    policy_file = tmp_path / "test_policy.yaml"
    policy_content = """
metadata:
  policy_name: cli_test_policy
  version: "1.0"
rules:
  rate_limits: []
"""
    policy_file.write_text(policy_content, encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        validate_policy_cmd(str(policy_file))
    assert exc_info.value.code == 0
