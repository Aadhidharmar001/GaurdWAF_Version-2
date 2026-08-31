# Installation & Package Management Guide

GuardWAF is distributed via PyPI as a zero-dependency-bloat Python package compatible with Python **3.9 – 3.13**.

---

## 📦 Core Package Installation

To install the minimal, lightweight GuardWAF core engine:

```bash
pip install guardwaf
```

This includes the `@protect` decorator, YAML policy loader, local key manager, parameter digest verifier, and in-memory/SQLite state stores.

---

## 🧩 Optional Framework Extras

Install optional framework adapters and cloud storage backends as needed:

```bash
# LangChain Adapter
pip install "guardwaf[langchain]"

# LangGraph Adapter
pip install "guardwaf[langgraph]"

# CrewAI Adapter
pip install "guardwaf[crewai]"

# Model Context Protocol (MCP) Gateway
pip install "guardwaf[mcp]"

# Distributed Redis State Store
pip install "guardwaf[redis]"

# Prometheus & OpenTelemetry Observability
pip install "guardwaf[observability]"

# All Integrations & Extras
pip install "guardwaf[all]"
```
