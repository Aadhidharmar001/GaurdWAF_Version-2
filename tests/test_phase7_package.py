"""
Phase 7 Package & Distribution Integrity Test Suite.
Verifies pyproject.toml package metadata, build release scripts, and clean package importability.
"""

import os
import subprocess
import sys


def test_release_build_script():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "scripts/build_release.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "BUILD SUCCESSFUL" in res.stdout


def test_package_verification_script():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "scripts/verify_package_install.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "PACKAGE INSTALLATION VERIFICATION PASSED" in res.stdout
