
content = b"""[project]
name = "mcpv"
version = "0.2.0"
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
"""

with open("pyproject.toml", "wb") as f:
    f.write(content.strip())
    
print("Clean pyproject.toml written.")
