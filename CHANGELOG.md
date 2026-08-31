# GuardWAF Release Changelog

## [1.0.0] - Phase 6 Release (Production Deployment & Operations)

### Added
- **Production AWS Infrastructure**: Terraform Infrastructure-as-Code blueprints for VPC subnets, ECS Fargate, ALB, RDS PostgreSQL, ElastiCache Redis, AWS Secrets Manager, and CloudWatch.
- **Security-Hardened Dockerfile**: Multi-stage build with non-root unprivileged execution (`UID 10001`) and HTTP health probes.
- **CI/CD Pipeline**: GitHub Actions workflow with 8 automated stages including secret scanning (`scripts/scan_secrets.py`), dependency vulnerability checks, Software Bill of Materials (SBOM) generation (`scripts/generate_sbom.py`), container security scans, and staging smoke tests (`scripts/smoke_test.py`).
- **Database Migration Safety**: Atomic migration locking, pre-migration snapshot validation, schema compatibility checks, and rollback safety (`infra/scripts/migrate_db.py`).
- **Flagship Customer Operations AI Agent**: End-to-end customer support demonstration (`examples/flagship_customer_ops_agent.py`) governing 8 real-world business scenarios.
- **External Developer Quickstart**: Self-contained example (`examples/quickstart_agent/`) and integration guide (`docs/external_developer_guide.md`) verified to onboard external developers in under 15 minutes.
- **Observability Engine**: Prometheus & CloudWatch metric exporters in `guardwaf/telemetry/metrics.py`.
- **Incident Response & Recovery Runbook**: Detailed operational procedures in `docs/operations/runbook.md`.
