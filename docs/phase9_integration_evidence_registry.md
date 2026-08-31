# GuardWAF Beta Integration Evidence Registry

This registry tracks the empirical validation status of every framework adapter and runtime integration.

---

## 📊 Integration Status Registry

| Integration ID | Framework / Protocol | Version Tested | Environment | Internal Test Status | Simulated DX Status | External Developer Validation Status | Last Verified Date |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **INT_001** | Core Python `@protect` | Python 3.9 - 3.13 | Linux / macOS / Windows | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | 2026-08-29 |
| **INT_002** | LangChain Core | `langchain-core>=0.1.0` | Linux / Windows | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | 2026-08-29 |
| **INT_003** | LangGraph State Graph | `langgraph>=0.0.1` | Linux / Windows | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | 2026-08-29 |
| **INT_004** | CrewAI Task Tools | `crewai>=0.1.0` | Linux / macOS | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | 2026-08-29 |
| **INT_005** | MCP Gateway Proxy | MCP / FastMCP Spec | Linux / Windows | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | 2026-08-29 |
| **INT_006** | Custom Python Loop | Pure Python / Async | Linux / macOS / Windows | `INTERNAL_TESTED` | `SIMULATED` | `UNKNOWN` | 2026-08-29 |

---

## 📌 Canonical Evidence Status Definitions

- **`INTERNAL_TESTED`**: Verified via internal unit and integration Pytest suites in CI.
- **`SIMULATED`**: Verified via automated onboarding simulation scripts (`scripts/verify_package_install.py`).
- **`EXTERNAL_REPORTED`**: An external developer reported testing this integration.
- **`EXTERNAL_REPRODUCED`**: Maintainers successfully reproduced the external developer's integration report.
- **`EXTERNAL_VALIDATED`**: Confirmed independently working in third-party production or staging environments.
- **`FAILED`**: Integration failed external validation due to bug or incompatibility.
- **`UNKNOWN`**: No external evidence has been received yet.
