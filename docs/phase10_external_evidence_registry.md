# GuardWAF External Evidence Registry

This registry tracks the empirical validation status of each framework adapter across internal engineering, simulated testing, and external developer reporting.

---

## 📊 Adapter Validation Evidence Matrix

| Integration ID | Framework / Protocol | Version Tested | Internal Engineering Status | Simulated DX Status | External Reported Status | External Reproduced Status | External Validated Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **INT_001** | Core Python `@protect` | Python 3.9 - 3.13 | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| **INT_002** | LangChain Core | `langchain-core>=0.1.0` | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| **INT_003** | LangGraph State Graph | `langgraph>=0.0.1` | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| **INT_004** | CrewAI Task Tools | `crewai>=0.1.0` | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| **INT_005** | MCP Gateway Proxy | MCP / FastMCP Spec | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| **INT_006** | Custom Python Loop | Pure Python / Async | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |

---

## 📌 Status Classification Definitions

- **`INTERNAL_TESTED`**: Verified via internal unit and integration Pytest suites in CI.
- **`SIMULATED`**: Verified via automated onboarding simulation scripts (`scripts/verify_package_install.py`).
- **`EXTERNAL_REPORTED`**: An external developer reported testing this integration.
- **`EXTERNAL_REPRODUCED`**: Maintainers successfully reproduced the external developer's integration report locally.
- **`EXTERNAL_VALIDATED`**: Confirmed independently working in third-party production or staging environments.
- **`FAILED`**: Integration failed external validation due to a bug or incompatibility.
- **`UNKNOWN`**: No external evidence has been received yet.
