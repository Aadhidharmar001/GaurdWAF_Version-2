# Contributing to GuardWAF

Thank you for your interest in contributing to GuardWAF!

## Security Guidelines & Code Quality
- All code changes must pass `pytest` and linting (`ruff check .`, `flake8 .`).
- Never introduce fallback hardcoded secrets. All production secrets must come from environment variables.
- Never alter fail-closed security invariants or weaken parameter digest verification.

## Submitting Pull Requests
1. Fork the repository and create a feature branch.
2. Run the test suite: `pytest`.
3. Run the secret scanner: `python scripts/scan_secrets.py`.
4. Submit a pull request targeting `main`.
