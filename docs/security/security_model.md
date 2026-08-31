# GuardWAF Security Model & Trust Boundaries

## Threat Model & Security Guarantees

### 1. GuardWAF Guarantees
- **Pre-Execution Interception**: Blocked actions never execute downstream Python function bodies or tool APIs.
- **Token Replay Protection**: HITL approval tokens are single-use (`EXECUTED` state transition) and cryptographically bound to canonical parameter digests (`SHA-256`).
- **Parameter Integrity**: Parameter digest verification prevents parameter tampering between approval and execution.
- **Server-Side Tenant Isolation**: Multi-tenant organizations and RBAC permissions are enforced server-side.
- **Local Revocation Enforcement**: Revoked agents and locked-down tenants are blocked locally in $O(1)$ constant time.

### 2. GuardWAF Non-Guarantees (Out of Scope)
- **Same-Process Code Tampering**: Cannot prevent malicious Python code executing in the same process from monkey-patching Python runtime memory.
- **Downstream Side-Effect Idempotency**: Cannot guarantee downstream idempotency without downstream API idempotency keys.
- **Host Compromise**: Does not secure compromised underlying OS infrastructure.
