# GuardWAF External Developer Feedback Schema Specification

This document defines the JSON/YAML schema for ingesting structured feedback from external beta developers.

---

## 🔒 Privacy & Data Collection Limits
- **NO PROMPTS**: Never collect raw user prompts or agent conversation turns.
- **NO SECRETS**: Never collect API keys, secret keys, passwords, or JWT tokens.
- **NO PAYLOADS**: Never collect private database payloads or customer PII.

---

## 📄 JSON Schema Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GuardWAFBetaFeedback",
  "type": "object",
  "required": [
    "feedback_id",
    "date",
    "developer_type",
    "framework",
    "installation_success",
    "category"
  ],
  "properties": {
    "feedback_id": {
      "type": "string",
      "description": "Unique identifier for feedback entry (e.g. fb_2026_001)"
    },
    "date": {
      "type": "string",
      "format": "date-time"
    },
    "developer_type": {
      "type": "string",
      "enum": ["individual_dev", "startup_engineer", "enterprise_architect", "researcher", "hobbyist"]
    },
    "experience_level": {
      "type": "string",
      "enum": ["beginner", "intermediate", "advanced"]
    },
    "framework": {
      "type": "string",
      "enum": ["core_python", "langchain", "langgraph", "crewai", "mcp", "custom_loop"]
    },
    "integration_type": {
      "type": "string",
      "enum": ["decorator", "adapter", "gateway", "runtime_adapter"]
    },
    "installation_success": {
      "type": "boolean"
    },
    "time_to_first_protected_tool_seconds": {
      "type": "number"
    },
    "time_to_first_policy_block_seconds": {
      "type": "number"
    },
    "documentation_rating_1_to_5": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5
    },
    "category": {
      "type": "string",
      "enum": [
        "INSTALLATION_FAILURE",
        "DEPENDENCY_CONFLICT",
        "DOCUMENTATION_CONFUSION",
        "POLICY_CONFUSION",
        "FRAMEWORK_INTEGRATION_FAILURE",
        "MCP_COMPATIBILITY_ISSUE",
        "PERFORMANCE_CONCERN",
        "SECURITY_CONCERN",
        "FEATURE_REQUEST",
        "GENERAL_FEEDBACK"
      ]
    },
    "integration_friction": {
      "type": "string"
    },
    "would_use_again": {
      "type": "boolean"
    },
    "would_recommend": {
      "type": "boolean"
    },
    "freeform_feedback": {
      "type": "string"
    }
  }
}
```
