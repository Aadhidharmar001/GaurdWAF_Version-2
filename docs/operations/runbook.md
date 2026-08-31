# GuardWAF Production Operations, Incident Response & Recovery Runbook

## Emergency Contacts & Operational Severity

| Severity Level | Response Time SLA | Incident Example | Primary Escalation |
| :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | $< 15\text{ mins}$ | Control Plane down & Redis cluster failed; Security Attack | Security Lead & Infrastructure Engineer |
| **SEV-2 (High)** | $< 1\text{ hour}$ | High rate of cross-tenant or forged approval attempts | Security Operations Team |
| **SEV-3 (Medium)** | $< 4\text{ hours}$ | Degraded readiness probe or high DB latency | Platform Operations Team |

---

## Operational Alerts & Metric Thresholds

```text
High Auth Failure Rate (20+ failures in 1 min)
       │
       ▼
Security Alert: Potential Credential Spray Attack

Multiple Cross-Tenant Access Attempts (5+ in 1 min)
       │
       ▼
Critical Security Alert: Potential Identity Bypassing Attack

Control Plane Unhealthy (/health/ready returns 503)
       │
       ▼
Operations Alert: Database/Redis Connection Loss

Spike in Blocked Actions (100+ blocks in 1 min)
       │
       ▼
Potential AI Agent Prompt-Injection Attack Alert
```

---

## Standard Emergency Procedures

### 1. Emergency Tenant Lockdown
In the event of a compromised organization tenant:
```bash
# Execute emergency tenant lockdown via Control Plane CLI / API
python -m guardwaf.cli lockdown --tenant-id "org_compromised_id" --reason "Suspicious activity detected"
```

### 2. Emergency Agent Disable / Revocation
To immediately stop a rogue AI agent across all active edge runtimes in $< 1\text{ ms}$:
```bash
# Issue cryptographic revocation event
python -m guardwaf.cli revoke-agent --agent-id "agent_rogue_id" --tenant-id "org_tenant_id"
```

### 3. Database Backup & Point-in-Time Restore (RDS PostgreSQL)
- **Automatic Backups**: Continuous multi-AZ WAL archiving with 30-day retention.
- **Manual Point-in-Time Restore**:
  ```bash
  aws rds restore-db-instance-to-point-in-time \
      --source-db-instance-identifier guardwaf-prod-db \
      --target-db-instance-identifier guardwaf-prod-db-restored \
      --restore-time 2026-08-28T12:00:00Z
  ```

### 4. Redis Outage Response & State Recovery
- **Behavior**: GuardWAF SDK runtime enforcement continues safely using local in-process memory store.
- **Fail-Closed Guarantee**: GuardWAF **NEVER** fails open. If distributed state is unavailable and an action requires distributed verification, it is safely blocked.
- **Cluster Restart**:
  ```bash
  aws elasticache reboot-replication-group --replication-group-id guardwaf-prod-redis --reboot-instances
  ```

### 5. HMAC Secret & Signing Key Rotation
To rotate active signing keys without downtime:
```bash
# Register new key 'k2' alongside active key 'k1'
python -m guardwaf.cli rotate-keys --new-key-id "k2" --new-secret "new_secret_key_32bytes_long..."
```

### 6. Emergency Policy Rollback
To immediately revert an organization policy bundle to the previous signed version:
```bash
python -m guardwaf.cli rollback-policy --tenant-id "org_tenant_id" --target-version 4
```
