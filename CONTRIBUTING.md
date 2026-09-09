# Contributing to GuardWAF

Thank you for your interest in contributing to GuardWAF! We welcome contributions from developers, security researchers, and AI engineers.

GuardWAF is enterprise-grade security middleware. All code contributions must adhere to strict quality, security, and architectural standards.

---

## 🛠️ Development Setup

### Prerequisites
- Python 3.9, 3.10, 3.11, 3.12, or 3.13
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Aadhidharmar001/GaurdWAF_Version-2.git
cd GaurdWAF_Version-2
```

### 2. Create and Activate an Isolated Virtual Environment
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies in Editable Mode
```bash
pip install --upgrade pip
pip install -e ".[all]"
```

---

## 🧪 Running Tests & Quality Verification

Before submitting any pull request, ensure the full test suite and linters pass cleanly:

### 1. Run Unit & Integration Tests
```bash
pytest
```
*All 142+ tests must pass without errors.*

### 2. Run Code Linting & Style Checks
```bash
# Ruff linter
ruff check .

# Flake8 style verification
flake8 . --max-line-length=140 --ignore=E501,W503,E203

# Code formatting
ruff format .
```

### 3. Run Pre-Commit Secret Scanner
```bash
python scripts/scan_secrets.py
```
*Zero hardcoded secrets or credentials allowed.*

---

## 🛡️ Critical Security Invariants for Contributors

Every pull request must preserve GuardWAF's core security invariants:

1. **Zero Downstream Execution on Block**: If an action is blocked or requires approval, the downstream tool body must **never** be entered.
2. **Fail-Closed Default**: In the event of an unhandled exception, syntax ambiguity, or timeout, GuardWAF must deny the action.
3. **Hot-Path Independence**: The local evaluation engine (`GuardWAF.authorize()`) must never make synchronous network calls to external control planes or remote databases.
4. **Parameter Integrity**: Parameter digest checking (SHA-256) cannot be bypassed or made optional for HITL approvals.
5. **No Hardcoded Secrets**: Never commit API keys, private keys, database credentials, or test passwords.

---

## 🌿 Contribution Workflow

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make Focused, Atomic Commits**:
   Follow conventional commits (e.g., `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).

3. **Validate Changes Locally**:
   Run `pytest` and `python scripts/scan_secrets.py`.

4. **Submit a Pull Request**:
   - Open a PR against `main`.
   - Provide a clear description of the problem solved, implementation rationale, and test coverage added.
   - Link any related issues.

---

## 🔒 Security Vulnerabilities

If your contribution relates to a potential security vulnerability or bypass, **DO NOT** open a public pull request or issue. Follow our [Responsible Disclosure Policy](SECURITY.md) via GitHub Private Security Advisories.
