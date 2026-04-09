#!/bin/bash
# Cross-platform initialization script for MCP Vault
# Equivalent to init.ps1 for macOS/Linux
# Note: This is a development init script for git operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Initializing MCP Vault development environment..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3.10+ is required"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"

# Check/install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the uv environment
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "📦 Installing dependencies..."
cd "$PROJECT_ROOT"
uv sync

echo ""
echo "✅ Initialization complete!"
echo "👉 Run 'python -m mcpv install' to set up the vault."
