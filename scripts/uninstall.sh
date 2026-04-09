#!/bin/bash
# Cross-platform uninstall script for MCP Vault
# Equivalent to uninstall.ps1 for macOS/Linux

set -e

echo "🗑️  Starting MCP Vault Uninstallation..." 

# Configuration paths
CONFIG_DIR="$HOME/.gemini/antigravity"
CONFIG_FILE="$CONFIG_DIR/mcp_config.json"
BACKUP_FILE="$CONFIG_DIR/mcp_config.original.json"
ROOT_PATH_FILE="$CONFIG_DIR/root_path.txt"
BOOSTER_SCRIPT="$CONFIG_DIR/boost_launcher.sh"

# Platform-specific paths
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DESKTOP_DIR="$HOME/Desktop"
    # Also check for OneDrive-like redirect on macOS
    if [ -d "$HOME/Library/CloudStorage/OneDrive/Desktop" ]; then
        DESKTOP_DIR="$HOME/Library/CloudStorage/OneDrive/Desktop"
    fi
else
    # Linux - check for XDG Desktop or OneDrive
    if [ -n "$XDG_DESKTOP_DIR" ]; then
        DESKTOP_DIR="$XDG_DESKTOP_DIR"
    elif [ -d "$HOME/OneDrive/Desktop" ]; then
        DESKTOP_DIR="$HOME/OneDrive/Desktop"
    else
        DESKTOP_DIR="$HOME/Desktop"
    fi
fi

SHORTCUT="$DESKTOP_DIR/Antigravity Boost (mcpv)"

echo "📦 Stage 1: Uninstalling mcpv python package..."
# Check if uv is available
if command -v uv &> /dev/null; then
    echo "   Using uv to uninstall..."
    uv pip uninstall mcpv || true
else
    echo "   Using pip to uninstall..."
    pip uninstall mcpv -y || true
fi

echo "🗑️  Stage 2: Removing Desktop Shortcut..."
if [ -f "$SHORTCUT" ]; then
    rm -f "$SHORTCUT"
    echo "   -> Shortcut removed."
else
    echo "   -> Shortcut not found (already removed)."
fi

# Also remove .desktop file on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    LINUX_SHORTCUT="$DESKTOP_DIR/Antigravity Boost (mcpv).desktop"
    if [ -f "$LINUX_SHORTCUT" ]; then
        rm -f "$LINUX_SHORTCUT"
        echo "   -> Linux desktop file removed."
    fi
fi

echo "🔧 Stage 3: Restoring original MCP configuration..."
if [ -f "$BACKUP_FILE" ]; then
    if [ -f "$CONFIG_FILE" ]; then
        rm -f "$CONFIG_FILE"
    fi
    mv "$BACKUP_FILE" "$CONFIG_FILE"
    echo "   -> Successfully restored mcp_config.original.json to mcp_config.json"
else
    if [ -f "$CONFIG_FILE" ]; then
        rm -f "$CONFIG_FILE"
        echo "   -> Original backup not found. Cleaned up mcpv config."
    fi
fi

echo "🧹 Stage 4: Cleaning up booster scripts and configs..."
CLEANED=0
if [ -f "$ROOT_PATH_FILE" ]; then rm -f "$ROOT_PATH_FILE"; CLEANED=$((CLEANED+1)); fi
if [ -f "$BOOSTER_SCRIPT" ]; then rm -f "$BOOSTER_SCRIPT"; CLEANED=$((CLEANED+1)); fi

if [ $CLEANED -gt 0 ]; then
    echo "   -> Removed $CLEANED mcpv environment files."
else
    echo "   -> Everything already clean."
fi

echo ""
echo "🎉 Success! MCP Vault has been completely removed and Antigravity is restored to original state."
echo "👉 You can now safely close this terminal."
