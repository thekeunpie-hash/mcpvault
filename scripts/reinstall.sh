#!/bin/bash
# Cross-platform reinstall script for MCP Vault
# Equivalent to reinstall.ps1 for macOS/Linux

set -e

echo "🔄 Starting MCP Vault Reinstallation..."

# Kill any running mcpv processes
if command -v pkill &> /dev/null; then
    pkill -f "mcpv" 2>/dev/null || true
    pkill -f "python.*mcpv" 2>/dev/null || true
else
    # Fallback for systems without pkill
    killall -9 python 2>/dev/null || true
fi

# Clear PYTHONHOME to prevent build isolation errors
unset PYTHONHOME

echo "📦 Stage 1: Reinstalling package (updating libraries)..."
uv pip install . --system --reinstall

echo "🔧 Stage 2: Running setup (create shortcut, etc)..."
python -m mcpv install --force

echo ""
echo "✅ Reinstallation complete!"
