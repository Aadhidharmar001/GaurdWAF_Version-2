# GuardWAF Public Beta Developer Feedback Guide

Thank you for testing GuardWAF during our Public Developer Beta!

Your direct, honest feedback helps shape GuardWAF's core runtime ergonomics, policy configuration, and framework adapters.

---

> [!CAUTION]
> ### 🔒 Strict Zero-Sensitive-Data Rule
> GuardWAF is security middleware. **NEVER** include the following in your feedback or bug reports:
> - Production or test API keys / tokens
> - Database passwords or connection strings
> - Private customer or company data
> - Real LLM conversation prompts or confidential model outputs
> - Production JWTs or secret keys
> 
> *Always use sanitized placeholders (e.g. `sk_test_...`, `cust_001`, `alice@example.com`).*

---

## 🏷️ Category Selection

Please select **one** primary category for your report:

- [ ] `INSTALLATION_FAILURE` — `pip install` or wheel build failed
- [ ] `DEPENDENCY_CONFLICT` — Package conflict with existing AI libraries
- [ ] `DOCUMENTATION_CONFUSION` — Unclear, missing, or misleading docs
- [ ] `POLICY_CONFUSION` — Difficulty setting up YAML/Pydantic rules
- [ ] `FRAMEWORK_INTEGRATION_FAILURE` — Error using LangChain, LangGraph, CrewAI, or Custom adapter
- [ ] `MCP_COMPATIBILITY_ISSUE` — Error using FastMCP or standard MCP gateway
- [ ] `PERFORMANCE_CONCERN` — Unexpected latency on local enforcement hot path
- [ ] `SECURITY_CONCERN` — Potential security bypass or invariant issue
- [ ] `FEATURE_REQUEST` — Suggested rule type or integration
- [ ] `GENERAL_FEEDBACK` — Overall developer experience thoughts

---

## 📝 Developer Feedback Questions

When sharing your experience (via [GitHub Issues](https://github.com/Aadhidharmar001/GaurdWAF_Version-2/issues/new?template=beta_feedback.yml)), please answer the following 7 core questions:

### 1. Integration Tested
Which framework, agent loop, or protocol did you test with GuardWAF?
- [ ] Core Python functions (`@protect` decorator)
- [ ] LangChain (`LangChainAdapter`)
- [ ] LangGraph State Graph
- [ ] CrewAI (`CrewAIAdapter`)
- [ ] FastMCP / Standard Model Context Protocol (MCP)
- [ ] Custom Agent Loop / Other (please specify)

### 2. Installation Experience
- Was installation successful on your first attempt? (Yes / No)
- Which method did you use? (`git clone` / GitHub direct `pip install` / local wheel)
- Did you encounter any dependency conflicts with existing AI libraries?

### 3. First Policy Enforcement
- Did you successfully run a minimal policy enforcement within 5 minutes? (Yes / No)
- Did you observe blocked actions being intercepted before downstream tools executed?
- Did you verify that downstream execution count was zero on blocked calls?

### 4. Developer Experience & Usability
- What part of the setup, YAML policy schema, or SDK API felt confusing or unintuitive?
- Were the error messages (`GuardWAFSecurityError`, `GuardWAFHITLRequiredError`) descriptive and actionable?
- What documentation was missing or could be clearer?

### 5. Failure Modes & Bugs
- Did anything fail unexpectedly, crash, or throw an unhandled exception?
- If so, please provide sanitized reproduction code and traceback.

### 6. Deployment Intent
- Based on your testing, would you consider deploying GuardWAF in your staging or production agent workflows?
  - [ ] Yes, planning to deploy
  - [ ] Maybe, pending specific features/integrations
  - [ ] No, not a fit

### 7. Primary Adoption Barrier
What is the single biggest barrier preventing immediate adoption?
- [ ] None / Ready to adopt
- [ ] Missing specific framework adapter
- [ ] Configuration / YAML policy complexity
- [ ] Missing hosted / managed control plane
- [ ] Performance / latency concerns
- [ ] Existing in-house solution
- [ ] Other (please specify)

---

## 📬 How to Submit Feedback

1. **GitHub Issue Form (Recommended)**:
   Submit directly using our structured [Beta Feedback Form](../../.github/ISSUE_TEMPLATE/beta_feedback.yml).
2. **Pull Request**:
   If you have written an adapter fix or documentation improvement, submit a PR following [CONTRIBUTING.md](../../CONTRIBUTING.md).
3. **Private Security Findings**:
   If your feedback involves a potential security bypass or vulnerability, submit via [GitHub Private Security Advisories](../../SECURITY.md).
