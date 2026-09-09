# Installation & Package Management Guide

GuardWAF is currently in **Public Developer Beta** (Python **3.9 – 3.13**).

---

> [!NOTE]
> ### 📢 Public Beta Installation Notice
> During the public developer beta, GuardWAF is distributed directly via **GitHub source releases** and **pre-built release wheels**.
> 
> General release publication to the public Python Package Index (PyPI) via `pip install guardwaf` will occur upon completion of independent developer beta validation.
>
> Supported beta installation methods are documented below.

---

## 📦 Supported Beta Installation Methods

### Method 1: Install Directly from GitHub (Recommended for Beta Testers)
You can install GuardWAF directly from the official GitHub repository without cloning:

```bash
# Core package
pip install "git+https://github.com/Aadhidharmar001/GaurdWAF_Version-2.git"

# With specific framework extras (e.g. LangChain, LangGraph, MCP)
pip install "guardwaf[all] @ git+https://github.com/Aadhidharmar001/GaurdWAF_Version-2.git"
```

---

### Method 2: Build & Install Local Release Wheel
For air-gapped environments, CI pipelines, or offline testing:

```bash
# 1. Clone repository
git clone https://github.com/Aadhidharmar001/GaurdWAF_Version-2.git
cd GaurdWAF_Version-2

# 2. Build official wheel artifact
python scripts/build_release.py

# 3. Install the generated .whl package
pip install dist/guardwaf-1.0.0-py3-none-any.whl
```

---

### Method 3: Editable Development Installation
For contributors and developers modifying or extending GuardWAF adapters:

```bash
git clone https://github.com/Aadhidharmar001/GaurdWAF_Version-2.git
cd GaurdWAF_Version-2

# Create isolated virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with all development and test dependencies
pip install -e ".[all]"
```

---

## 🧩 Optional Framework Extras

When installing via GitHub or local editable mode, you can select specific extras:

| Extra Flag | Description | Included Packages |
| :--- | :--- | :--- |
| `guardwaf[langchain]` | LangChain tool interceptor adapter | `langchain-core` |
| `guardwaf[langgraph]` | LangGraph state graph node gate | `langgraph` |
| `guardwaf[crewai]` | CrewAI agent tool adapter | `crewai` |
| `guardwaf[mcp]` | FastMCP and standard MCP gateway | `mcp`, `fastmcp` |
| `guardwaf[redis]` | Distributed Redis session & token cache | `redis` |
| `guardwaf[all]` | Complete bundle of all adapters and extras | All optional dependencies |

---

## 🚀 Verifying Your Installation

Verify that the GuardWAF engine and CLI/SDK are functional:

```bash
python -c "import guardwaf; print('GuardWAF Version:', guardwaf.__version__)"
```

Expected output:
```text
GuardWAF Version: 1.0.0
```
