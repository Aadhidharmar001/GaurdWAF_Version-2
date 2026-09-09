# GuardWAF Changelog & Versioning Policy

This document defines GuardWAF's changelog maintenance strategy and semantic versioning rules.

---

## 🏷️ Semantic Versioning

GuardWAF adheres to [Semantic Versioning 2.0.0](https://semver.org/):

`MAJOR.MINOR.PATCH[-PRERELEASE]`

- **MAJOR**: Breaking API or security invariant changes (e.g., changes to policy format, ActionEnvelope schema, or SDK method signatures).
- **MINOR**: Backward-compatible new capabilities, framework adapters, rule types, or non-breaking features.
- **PATCH**: Backward-compatible bug fixes, security patches, performance improvements, or documentation updates.
- **PRERELEASE**: Pre-general-availability releases designated with `-beta.N` or `-rc.N` (e.g., `1.0.0-beta.1`).

---

## 📜 Changelog Structure & Sections

GuardWAF follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Every release entry in [CHANGELOG.md](../CHANGELOG.md) must categorize changes into:

- **`Added`**: New features, integrations, or policy rule types.
- **`Changed`**: Changes in existing functionality or default behaviors.
- **`Deprecated`**: Soon-to-be-removed features.
- **`Removed`**: Features removed in this release.
- **`Fixed`**: Bug fixes and stability improvements.
- **`Security`**: Vulnerability mitigations, security invariant hardening, and dependency CVE fixes.

---

## 🛡️ Honesty Invariant for Changelogs

1. Never log a capability in the changelog unless the implementation code and tests exist in the repository.
2. Never claim third-party certifications, production customer adoptions, or external benchmarks in release notes unless backed by verified public evidence.
3. Every security patch must reference the relevant internal tracking ID or GitHub Security Advisory.
