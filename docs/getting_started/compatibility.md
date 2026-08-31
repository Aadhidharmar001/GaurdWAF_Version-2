# Framework Compatibility Matrix & Support Boundaries

GuardWAF provides universal runtime action governance across major agent frameworks and protocol standards.

---

## 📊 Compatibility Matrix

| Integration / Runtime | Tested Version | Extra Package Required | Support Level |
| :--- | :--- | :--- | :--- |
| **Core Python Functions** | Python 3.9 – 3.13 | None (`pip install guardwaf`) | **Native / Core** |
| **LangChain Tools** | `langchain-core >= 0.1.0` | `guardwaf[langchain]` | **Supported** |
| **LangGraph Nodes** | `langgraph >= 0.0.1` | `guardwaf[langgraph]` | **Supported** |
| **CrewAI Tasks** | `crewai >= 0.1.0` | `guardwaf[crewai]` | **Supported** |
| **MCP Gateways** | MCP Spec 2024-11-05 | `guardwaf[mcp]` | **Supported** |
| **Custom Agent Loops** | Pure Python | None (`pip install guardwaf`) | **Supported** |
