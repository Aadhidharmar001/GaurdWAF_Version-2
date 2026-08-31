# Framework Compatibility & Validation Matrix

This document tracks empirical compatibility across AI agent frameworks, protocols, and Python runtimes.

---

## 📊 Framework Compatibility Matrix

| Framework / Protocol | Version Tested | Integration Adapter | Internal Engineering Status | Automated CI Test Status | External Developer Validation Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Core Python Tools** | Python 3.9 – 3.13 | `@guardwaf.protect()` | `SUPPORTED` | `AUTOMATICALLY_TESTED` | `NOT_YET_VALIDATED` |
| **LangChain** | `langchain-core >= 0.1.0` | `LangChainAdapter` | `SUPPORTED` | `AUTOMATICALLY_TESTED` | `NOT_YET_VALIDATED` |
| **LangGraph** | `langgraph >= 0.0.1` | `LangGraphAdapter` | `SUPPORTED` | `AUTOMATICALLY_TESTED` | `NOT_YET_VALIDATED` |
| **CrewAI** | `crewai >= 0.1.0` | `CrewAIAdapter` | `SUPPORTED` | `AUTOMATICALLY_TESTED` | `NOT_YET_VALIDATED` |
| **Model Context Protocol (MCP)**| Standard & FastMCP Spec | `MCPGatewayProxy` | `SUPPORTED` | `AUTOMATICALLY_TESTED` | `NOT_YET_VALIDATED` |
| **Custom Agent Loops** | Pure Python / Async | `AgentRuntimeAdapter` | `SUPPORTED` | `AUTOMATICALLY_TESTED` | `NOT_YET_VALIDATED` |

---

## 📌 Status Classification Definitions

- **`SUPPORTED`**: Maintained, documented, and fully integrated with core ActionEnvelope engine.
- **`AUTOMATICALLY_TESTED`**: Verified continuously via automated Pytest test suite in CI pipeline.
- **`EXTERNALLY_VALIDATED`**: Confirmed working by independent third-party developers in public beta. *(Currently `NOT_YET_VALIDATED` until external feedback is received)*.
- **`EXPERIMENTAL`**: Early-stage adapter available for community feedback.
- **`NOT_YET_VALIDATED`**: Awaiting real-world developer validation.
