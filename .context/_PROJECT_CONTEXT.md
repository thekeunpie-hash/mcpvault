# Project Context

Generated: 2026-04-08T09:04:49.343824

Files analyzed: 3

---


## pyproject.toml
```
[project]
name = "mcpv"
version = "0.3.5"
description = "MCP Vault: Secure Gateway & Booster for Antigravity"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=0.1.0",
    "mcp>=1.0.0",
    "typer>=0.9.0",
]

[project.scripts]
mcpv = "mcpv.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

...
```

## README.md
```
# ⚡ MCP Vault (`mcpv`)

> **The Ultimate Performance Booster for AI Agents**  
> _"Reduce system lag by 99%, eliminate loading times, and cut token costs by 90%."_

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-F7CA3F.svg?style=flat-square&logo=python&logoColor=black)
![Platform](https://img.shields.io/badge/OS-Windows-0078D6.svg?style=flat-square&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Accelerated-brightgreen.svg?style=flat-square)

</div>

<div align="right">
  <a href="README_KR.md">🇰🇷 한국어</a> | <a href="README_CN.md">🇨🇳 中文</a> | <a href="README_RU.md">🇷🇺 Русский</a>
</div>

<br>

> [!CAUTION]
> **⚠️ Compatibility Warning**<br>
> Currently, this project ONLY supports **Windows** OS and the **Antigravity** agent environment.

<br>

## ❓ Why `mcpv`?

Have you ever felt this while using AI Agents (Antigravity, Cursor)?
> *"Why is it so heavy?"*  
> *"It froze again..."*  
> *"Why are the token costs so high?"*

`mcpv` is not just a tool. It is a **Turbo Engine** for your agent.

<br>

### 🏎️ Overwhelming Performance Difference

| Feature | 😫 Without `mcpv` (Before) | ⚡ With `mcpv` (After) | 📈 Effect |
| :--- | :--- | :--- | :--- |
| **Speed** | No GPU, Laggy UI | **Forced GPU Acceleration, Smooth** | **100x** Perceived Speed |
| **Scalability** | Truncates at 100 tools | **Unlimited Tools (Summary + JIT)** | **∞** Capacity |
| **Loading** | Wait 60s+ every time | **Instant Startup (Local Cache)** | **Zero** Latency |
| **Cost** | Resend full context | **Smart Block / Deduplication** | **90%** Savings |

<br>

---

## ✨ 3 Core Features

### 1️⃣ Booster Injection (Physical Acceleration)
**"Unlock hardware limits with one line"**
- **Forced GPU Activation**: Injects hidden rendering acceleration flags (`--enable-gpu-rasterization`).
- **Permission Bypass**: Drops Admin rights to fix drag-and-drop & UI bugs, and bypasses permiss...
```

## Directory Structure
```
├── PLAN
│   └── LOGBOOK.md
├── src
│   └── mcpv
│       ├── __init__.py
│       ├── __main__.py
│       ├── dashboard.py
│       ├── main.py
│       ├── server.py
│       ├── valve.py
│       └── vault.py
├── tests
│   └── test_timeout_protection.py
├── Hello.md
├── README.md
├── README_CN.md
├── README_KR.md
├── README_RU.md
├── UNINSTALL_KR.md
├── check.bat
├── check_bytes.py
├── convert.py
├── create_toml.py
├── force_clean.py
├── init.ps1
├── pat_result.txt
├── push.bat
├── pyproject.toml
├── reinstall.ps1
├── revert.py
├── search_pat.py
├── stdout
├── uninstall.ps1
├── uv.lock
└── validate_toml.py
```
