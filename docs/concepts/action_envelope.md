# Transport-Neutral ActionEnvelope Specification

`ActionEnvelope` is the universal, transport-neutral JSON representation of an AI agent tool action evaluated by GuardWAF.

---

## 📄 ActionEnvelope Fields

```json
{
  "envelope_id": "env_9a8b7c6d5e",
  "timestamp": "2026-08-28T20:00:00Z",
  "tenant_id": "org_fintech",
  "agent_id": "payment_bot",
  "principal_id": "user_alex",
  "session_id": "sess_1029",
  "tool_name": "issue_refund",
  "parameters": {
    "customer_id": "cust_101",
    "amount": 500.0
  },
  "parameter_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

## 🔒 Canonical Digest Algorithm
1. Canonicalize parameters: `json.dumps(params, sort_keys=True, separators=(',', ':'))`.
2. Compute SHA-256 hash digest.
3. Compare digest against signed Action Grant / HITL token to guarantee parameter integrity.
