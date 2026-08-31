"""
Phase 7 Framework Integrations Test Suite.
Verifies LangChain, LangGraph, CrewAI, FastMCP, and Custom Agent integration examples.
"""

import pytest
import sys
import os
import subprocess

def run_integration_script(path: str):
    env = {**os.environ, "PYTHONPATH": "."}
    cmd = [sys.executable, path]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0

def test_langchain_integration_example():
    run_integration_script("examples/integrations/langchain_agent/main.py")

def test_langgraph_integration_example():
    run_integration_script("examples/integrations/langgraph_agent/main.py")

def test_crewai_integration_example():
    run_integration_script("examples/integrations/crewai_agent/main.py")

def test_mcp_integration_example():
    run_integration_script("examples/integrations/mcp_server/main.py")

def test_custom_agent_integration_example():
    run_integration_script("examples/integrations/custom_agent/main.py")
