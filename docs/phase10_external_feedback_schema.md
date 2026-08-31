# GuardWAF Phase 10 External Feedback Schema Specification

This document specifies the anonymized feedback schema and sample size rules for Phase 10 developer validation.

---

## 📊 Sample-Size Discipline Rules

To ensure GuardWAF never makes exaggerated claims from small sample sizes, all analytics and dashboards enforce:

- **`n < 5`**: **Qualitative Signal Only**. (Report as *"4 of 5 participants preferred X; early signal, insufficient sample (n=5)"*).
- **`5 <= n < 10`**: **Early Directional Signal**.
- **`10 <= n < 30`**: **Moderate Evidence**.
- **`n >= 30`**: **Strong Directional Evidence**.

---

## 🏷️ 17 Feedback Categories

1. `INSTALLATION`
2. `QUICKSTART`
3. `DOCUMENTATION`
4. `POLICY`
5. `IDENTITY`
6. `HITL`
7. `MCP`
8. `LANGCHAIN`
9. `LANGGRAPH`
10. `CREWAI`
11. `PERFORMANCE`
12. `SECURITY`
13. `DEPLOYMENT`
14. `DASHBOARD`
15. `VALUE_PROPOSITION`
16. `FEATURE_REQUEST`
17. `GENERAL`

---

## 📄 JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GuardWAFPhase10Feedback",
  "type": "object",
  "required": [
    "feedback_id",
    "date",
    "developer_type",
    "framework",
    "category",
    "would_deploy_production"
  ],
  "properties": {
    "feedback_id": {"type": "string"},
    "date": {"type": "string", "format": "date-time"},
    "developer_type": {
      "type": "string",
      "enum": ["individual_dev", "startup_engineer", "enterprise_architect", "researcher", "hobbyist"]
    },
    "framework": {
      "type": "string",
      "enum": ["core_python", "langchain", "langgraph", "crewai", "mcp", "custom_loop"]
    },
    "category": {
      "type": "string",
      "enum": [
        "INSTALLATION", "QUICKSTART", "DOCUMENTATION", "POLICY", "IDENTITY", "HITL",
        "MCP", "LANGCHAIN", "LANGGRAPH", "CREWAI", "PERFORMANCE", "SECURITY",
        "DEPLOYMENT", "DASHBOARD", "VALUE_PROPOSITION", "FEATURE_REQUEST", "GENERAL"
      ]
    },
    "time_to_first_protected_tool_seconds": {"type": "number"},
    "time_to_first_policy_block_seconds": {"type": "number"},
    "would_deploy_production": {"type": "string", "enum": ["yes", "maybe", "no"]},
    "primary_adoption_barrier": {
      "type": "string",
      "enum": [
        "none", "security_concerns", "missing_framework", "configuration_complexity",
        "missing_hosted_control_plane", "performance_concerns", "unclear_value_proposition",
        "existing_in_house_solution"
      ]
    },
    "qualitative_feedback": {"type": "string"}
  }
}
```
