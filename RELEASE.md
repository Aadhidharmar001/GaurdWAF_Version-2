# GuardWAF Release Engineering Procedure

This document outlines the step-by-step process for building, verifying, and publishing GuardWAF release packages to PyPI.

---

## 🚀 Release Process

### 1. Version Bump
Update the version string in `pyproject.toml`:
```toml
[project]
version = "1.0.0"
```

### 2. Build Release Artifacts
Run the automated release builder:
```bash
python scripts/build_release.py
```
This generates source distribution (`sdist`) and wheel (`.whl`) files in `dist/`.

### 3. Verify Package Integrity in Clean Environment
Validate that the wheel installs and executes in an isolated environment without dev dependencies:
```bash
python scripts/verify_package_install.py
```

### 4. Check Package Metadata with Twine
```bash
twine check dist/*
```

### 5. Publish to PyPI
```bash
twine upload dist/*
```
