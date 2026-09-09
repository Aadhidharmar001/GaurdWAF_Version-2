# GuardWAF Release Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-beta.1] - 2026-09-09 — Public Developer Beta Readiness

### Added
- **Public Developer Beta Starter Kit**: Streamlined onboarding starter project in `examples/external_beta/` with verified downstream execution tracking.
- **Modern GitHub Issue Forms**: Interactive YAML templates for Bug Reports (`bug_report.yml`), Feature Requests (`feature_request.yml`), and Beta Feedback (`beta_feedback.yml`) with strict zero-sensitive-data warnings.
- **Beta Release Readiness Checklist**: 12-item pre-release quality gate documented in `docs/public_beta_release_checklist.md`.
- **Changelog & Versioning Policy**: Defined semantic versioning strategy in `docs/changelog_policy.md`.
- **Comprehensive Developer Documentation**: Detailed installation paths covering GitHub direct install, local wheel builds, and editable development setups in `docs/getting_started/installation.md`.

### Changed
- **Enterprise WAF Framing**: Overhauled `README.md` to clearly position GuardWAF as an Enterprise Agent WAF & Action Guardrail Gateway, contrasting action authorization with traditional LLM output guardrails.
- **Responsible Disclosure Process**: Upgraded `SECURITY.md` to use GitHub Private Security Advisories directly, removing placeholder emails and defining 48-hour response SLAs.
- **Contributor Experience**: Expanded `CONTRIBUTING.md` with complete virtualenv setup, linting commands (`ruff`, `flake8`), security invariants, and branch workflows.
- **Code of Conduct**: Fully aligned `CODE_OF_CONDUCT.md` with Contributor Covenant v2.1 standards.

### Security
- **Downstream Zero-Execution Invariant**: Re-verified across all core SDK interceptors and external starter kits.
- **Strict Privacy Sanitization**: Verified telemetry is OFF by default with zero collection of prompts, tool arguments, or customer payloads.

---

## [1.0.0] - Phase 6–10 Release (Production Architecture & Product Intelligence)

### Added
- **Phase 10 External Validation Infrastructure**: Evidence registry (`docs/phase10_external_evidence_registry.md`), feedback schemas (`docs/phase10_external_feedback_schema.md`), and automated learning dashboard (`scripts/product_learning_dashboard.py`).
- **Phase 9 Product Intelligence Framework**: 4-stream evidence separation (engineering, internal validation, opt-in telemetry, external feedback) ensuring zero simulated data leakage into external metrics.
- **Phase 8 Public Beta Validation**: Interactive Playground (`examples/playground/main.py`) demonstrating live tool interception, HITL gates, prompt injection defense, and emergency agent revocation.
- **Phase 7 Public Beta Platform**: Reorganized documentation portal, verified 60-second quickstarts, and framework compatibility matrix.
- **Phase 6 Production Cloud Infrastructure**: Terraform blueprints for AWS ECS Fargate, ALB, RDS PostgreSQL, ElastiCache Redis, and Secrets Manager.
- **8-Stage CI/CD Automation**: GitHub Actions pipeline covering code quality, pytest test suite, SBOM generation, secret scanning, container build, staging smoke tests, and production approval gates.
- **Core Security Engine (Phases 1–5)**: Pre-execution `@protect` decorator, declarative YAML/Pydantic rules, SHA-256 parameter digests, HMAC approval tokens, nonce replay protection, $O(1)$ agent kill switch, and multi-tenant isolation.
- **Framework Adapters**: Production-tested adapters for LangChain, LangGraph, CrewAI, and Model Context Protocol (MCP / FastMCP).

---

## [0.1.0] - Initial Prototype
- Core `@protect` decorator and initial policy evaluation prototypes.
