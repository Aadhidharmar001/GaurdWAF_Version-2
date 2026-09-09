# GuardWAF Public Beta Release Checklist

This document defines the release readiness criteria that must be verified before tagging and releasing any public beta build of GuardWAF.

---

## 📋 Release Readiness Gate

All items must be verified and checked before an official release tag is created:

- [ ] **Tests Passing**: Full test suite passes across all supported Python versions (`python -m pytest`).
- [ ] **Secret Scan Passing**: Zero hardcoded secrets, private keys, or credentials in the codebase (`python scripts/scan_secrets.py`).
- [ ] **Dependency Scan & SBOM Passing**: Dependencies scanned for known CVEs and SPDX 2.3 SBOM generated (`python scripts/generate_sbom.py`).
- [ ] **Package Build Passing**: Source distribution and wheel packages build cleanly without warnings (`python scripts/build_release.py`).
- [ ] **Clean Installation Passing**: Wheel installs and executes in an isolated environment without development dependencies (`python scripts/verify_package_install.py`).
- [ ] **60-Second Quickstart Passing**: Minimal quickstart snippet runs out of the box with zero configuration (`python quickstart.py`).
- [ ] **Documentation Reviewed**: All documentation links, guides, and architectural descriptions are verified and up to date.
- [ ] **Security Policy Available**: Responsible disclosure policy and reporting channels published in [SECURITY.md](../SECURITY.md).
- [ ] **Contribution Guide Available**: Development workflow, style guide, and invariant rules published in [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] **Known Limitations Documented**: Clear documentation of in-process threat boundaries, host security scope, and non-goals in [security_model.md](security/security_model.md).
- [ ] **Beta Status Documented Honestly**: Public developer beta status is explicitly noted in README and docs, with zero fabricated adoption claims.
- [ ] **No External Validation Claims Without Evidence**: External validation metrics remain marked as `UNKNOWN / NOT YET MEASURED / AWAITING REAL EXTERNAL EVIDENCE` until verified third-party evidence is collected.

---

## 🔍 Pre-Release Validation Commands

Run this sequence to verify all engineering criteria locally:

```bash
# 1. Automated Test Suite (142+ tests)
python -m pytest

# 2. Code Linting & Style Verification
ruff check .
flake8 . --max-line-length=140 --ignore=E501,W503,E203

# 3. Secret Scanning (Zero Hardcoded Secrets)
python scripts/scan_secrets.py

# 4. Package Release Artifacts Build
python scripts/build_release.py

# 5. Clean-Environment Wheel Installation Verification
python scripts/verify_package_install.py

# 6. External Beta Starter Kit Verification
python examples/external_beta/main.py

# 7. Product Learning Dashboard Verification
python scripts/product_learning_dashboard.py
```

---

## 🚫 Release Prohibitions (Beta Safeguards)

- **DO NOT** publish packages to public PyPI without explicit maintainer approval.
- **DO NOT** create a production release tag if any test or security scan fails.
- **DO NOT** deploy unreviewed infrastructure changes directly to production clusters.
- **DO NOT** convert external metrics from `UNKNOWN` to `VALIDATED` without independent evidence logs in `docs/phase10_external_evidence_registry.md`.
