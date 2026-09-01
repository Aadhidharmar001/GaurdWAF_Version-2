# GuardWAF — Agent Action Authorization & Runtime Governance Platform

[![CI Status](https://github.com/aadhidharmar001/guardwaf/actions/workflows/ci_cd.yml/badge.svg)](https://github.com/aadhidharmar001/guardwaf/actions/workflows/ci_cd.yml)
[![PyPI Version](https://img.shields.io/pypi/v/guardwaf.svg)](https://pypi.org/project/guardwaf/)
[![Python Versions](https://img.shields.io/pypi/pyversions/guardwaf.svg)](https://pypi.org/project/guardwaf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security Policy](https://img.shields.io/badge/Security-Policy-blue.svg)](SECURITY.md)

> **GuardWAF is a runtime authorization and governance layer for AI agents that intercepts tool actions before execution and enforces policy, identity, delegated authority, human approval, and emergency revocation—without adding network calls to the agent's local enforcement hot path.**

---

## 💥 The AI Agent Security Problem

Autonomous AI agents equipped with tools can execute destructive side effects on databases, payment APIs, Cloud infrastructure, and enterprise SaaS systems. Traditional Web Application Firewalls (WAFs) inspect incoming HTTP requests, but **cannot govern non-deterministic tool actions chosen dynamically by LLMs**.

```text
WITHOUT GUARdWAF:

  LLM Agent ────────► Selects Tool ────────► Executes Direct Side Effect 💥
  (Autonomous)      issue_refund($50,000)   (Database Mutated / Money Sent)


WITH GUARdWAF:

  LLM Agent ────────► GuardWAF Interception ───► Policy & Identity Check
  (Autonomous)      issue_refund($50,000)         (Hot Path < 1.0 ms)
                                                          │
                                      ┌───────────────────┼───────────────────┐
                                      ▼                   ▼                   ▼
                                 [ ALLOWED ]         [ BLOCKED ]       [ REQUIRE HITL ]
                                      │                   │                   │
                                      ▼                   ▼                   ▼
                              Tool Executes       Zero Downstream     Action Suspended
                              Side Effect         Execution (0)       for Human Approval
```

---

## 🔌 Framework Compatibility Matrix

GuardWAF governs AI agent actions universally across all major agent frameworks and protocol standards:

| Framework / Protocol | Version Tested | Integration Adapter | Status |
| :--- | :--- | :--- | :--- |
| **Core Python Tools** | Python 3.9 – 3.13 | `@guardwaf.protect()` decorator | **Supported** |
| **LangChain** | `langchain-core >= 0.1.0` | `LangChainAdapter` | **Supported** |
| **LangGraph** | `langgraph >= 0.0.1` | `LangGraphAdapter` | **Supported** |
| **CrewAI** | `crewai >= 0.1.0` | `CrewAIAdapter` | **Supported** |
| **Model Context Protocol (MCP)**| Standard & FastMCP Spec | `MCPGatewayProxy` / `secure_server` | **Supported** |
| **Custom Agent Loops** | Pure Python / Async | `AgentRuntimeAdapter` | **Supported** |

---

## ⚡ Quickstart (60 Seconds)

### 1. Install GuardWAF
```bash
pip install guardwaf
```

### 2. Protect Your First Tool
```python
from guardwaf import GuardWAF, protect, GuardWAFSecurityError
from guardwaf.core.models import PolicyConfig, PolicyRules, BulkThresholdRule

# 1. Define Action Policy
rules = PolicyRules(
    bulk_thresholds=[
        BulkThresholdRule(tool="issue_refund", param_name="amount", max_value=100.0)
    ]
)
policy = PolicyConfig(metadata={"policy_name": "refund_policy"}, rules=rules)

# 2. Initialize GuardWAF Engine
waf = GuardWAF(policy=policy, secret_key="production_secret_key_32bytes_long_min")


# 3. Protect Agent Tool Body
@protect(tool_name="issue_refund", client=waf)
def issue_refund(customer_id: str, amount: float):
    print(f"✅ Executing Refund: ${amount} to {customer_id}")
    return {"status": "SUCCESS", "refund_id": "ref_1002"}


# 4. Execute Actions within Session
with waf.session(session_id="sess_demo_1"):
    # SAFE ACTION: Allowed ($50.00)
    issue_refund("cust_101", 50.0)

    # DANGEROUS ACTION: Blocked before execution ($5,000.00)
    try:
        issue_refund("cust_101", 5000.0)
    except GuardWAFSecurityError as err:
        print(f"🚨 GUARdWAF BLOCKED DANGEROUS ACTION: {err}")
```

**Output:**
```text
✅ Executing Refund: $50.0 to cust_101
🚨 GUARdWAF BLOCKED DANGEROUS ACTION: Action 'issue_refund' blocked by GuardWAF policy: Bulk Threshold Exceeded: Parameter 'amount' value 5000.0 exceeds max 100.0
```

---

## 🎯 Hero Feature: Interactive GuardWAF Playground

Test GuardWAF's real-time interception, human-in-the-loop approval, and prompt injection defense interactively:

```bash
python examples/playground/main.py
```

---

## ⚡ Performance Metrics

| Benchmark | Latency / Throughput | Target |
| :--- | :--- | :--- |
| **Local Policy Enforcement** | **6,478 req/sec** | $> 1,000\text{ req/sec}$ |
| **Hot-Path p50 Latency** | **0.1304 ms** | $< 1.0\text{ ms}$ |
| **Hot-Path p95 Latency** | **0.2664 ms** | $< 2.0\text{ ms}$ |
| **Hot-Path p99 Latency** | **0.4535 ms** | $< 5.0\text{ ms}$ |
| **100 Concurrent Agents** | **6,132 req/sec** | $> 1,000\text{ req/sec}$ |

---

## 📚 Documentation Portal Map

- [Getting Started & Installation](docs/getting_started/installation.md)
- [60-Second Quickstart Guide](docs/getting_started/quickstart.md)
- [Framework Compatibility Matrix](docs/getting_started/compatibility.md)
- [ActionEnvelope Transport Neutral Spec](docs/concepts/action_envelope.md)
- [Policy Configuration & Rules](docs/concepts/policies.md)
- [Human-in-the-Loop Resumable Governance](docs/concepts/hitl.md)
- [Local $O(1)$ Revocation & Kill Switch](docs/concepts/revocation.md)
- [Security Model & Threat Boundaries](docs/security/security_model.md)
- [Production Deployment Guide (AWS ECS)](docs/production_deployment.md)
- [Public Beta Program Guide](docs/PUBLIC_BETA.md)

---

## ⚖️ License & Community
GuardWAF is open source software released under the [MIT License](LICENSE).
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Responsible Disclosure Policy](SECURITY.md)