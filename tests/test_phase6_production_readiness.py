"""
Phase 6 Automated Production Readiness & Security Test Suite.
Verifies CI/CD security scripts, migration safety checks, container readiness probes, secret scanning, and flagship agent integration.
"""

import pytest
import sys
import subprocess
from guardwaf import GuardWAF, protect, GuardWAFSecurityError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule
from scripts.scan_secrets import main as run_secret_scanner
from scripts.smoke_test import run_smoke_tests
from infra.scripts.migrate_db import run_migrations

def test_secret_scanner_execution():
    result = run_secret_scanner()
    assert result == 0

def test_db_migration_dry_run_check():
    result = run_migrations(dry_run=True)
    assert result is True

def test_smoke_test_suite_execution():
    result = run_smoke_tests()
    assert result is True

def test_flagship_customer_ops_agent_scenarios():
    from examples.flagship_customer_ops_agent import run_flagship_demo
    run_flagship_demo()
