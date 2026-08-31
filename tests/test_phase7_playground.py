"""
Phase 7 Hero Feature Playground Test Suite.
Verifies examples/playground/main.py end-to-end execution.
"""

import pytest
import sys
import os
import subprocess

def test_playground_hero_feature_execution():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "examples/playground/main.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "PLAYGROUND HERO DEMO COMPLETE" in res.stdout
