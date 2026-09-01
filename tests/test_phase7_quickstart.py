"""
Phase 7 60-Second Quickstart Test Suite.
Verifies examples/60_second_quickstart/main.py execution and YAML policy loading.
"""

import os
import subprocess
import sys


def test_60_second_quickstart_execution():
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, "examples/60_second_quickstart/main.py"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0
    assert "QUICKSTART COMPLETE" in res.stdout
