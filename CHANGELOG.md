# Changelog

All notable changes to MCP Vault (`mcpv`) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-04-08

### 🎉 Major Changes

#### Cross-Platform Support (Windows, macOS, Linux)

This release introduces full cross-platform support, transforming MCP Vault from a Windows-only tool to a universal solution for AI agent acceleration.

**New Platform Abstraction Layer:**
- Added [`src/mcpv/platform_abstraction.py`](src/mcpv/platform_abstraction.py) - Core module for OS detection and platform-specific operations
- `PlatformInfo` class provides unified interface for:
  - Platform detection (Windows/macOS/Linux)
  - Path resolution (AppData, Library, XDG directories)
  - Executable naming (`.exe` on Windows, none on Unix)
  - Script extensions (`.bat` vs `.sh`)
  - Shell command generation (`cmd.exe` vs `bash`)
  - Process management (window hiding flags)

**Path Handling Improvements:**
- Windows: OneDrive Desktop redirect detection via registry
- macOS: `~/Library/Application Support` paths
- Linux: XDG specification compliance (`~/.local/share`)
- Unified config directory: `~/.gemini/antigravity` (all platforms)

**New Shell Scripts:**
- [`scripts/init.sh`](scripts/init.sh) - Development initialization for macOS/Linux
- [`scripts/uninstall.sh`](scripts/uninstall.sh) - Cross-platform uninstaller
- [`scripts/reinstall.sh`](scripts/reinstall.sh) - Cross-platform reinstaller

**Desktop/Launcher Support:**
- Windows: `.lnk` shortcuts with OneDrive Desktop support
- macOS: `.command` files in Applications folder
- Linux: `.desktop` files (XDG standard)

### 📦 Updated Files

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcpv/platform_abstraction.py` | NEW | Core platform abstraction module |
| `src/mcpv/platform_utils.py` | MODIFIED | Enhanced with cross-platform desktop detection |
| `src/mcpv/vault.py` | MODIFIED | Uses platform_info for paths and executables |
| `src/mcpv/server.py` | MODIFIED | Uses platform_info for config directory |
| `scripts/init.sh` | NEW | macOS/Linux init script |
| `scripts/uninstall.sh` | NEW | macOS/Linux uninstall script |
| `scripts/reinstall.sh` | NEW | macOS/Linux reinstall script |
| `tests/test_platform_abstraction.py` | NEW | 31 unit tests for platform abstraction |
| `README.md` | MODIFIED | Updated with multi-platform documentation |
| `pyproject.toml` | MODIFIED | Version bump to 0.4.0, added classifiers |

### 🧪 Testing

- Added 31 unit tests for `platform_abstraction` module
- All tests pass on Windows (mocked tests for macOS/Linux)
- Integration tests verify actual system behavior

### 📝 Documentation

- Updated README.md with platform support matrix
- Added installation instructions for Windows, macOS, and Linux
- Documented platform-specific features and limitations

### 🔧 Technical Changes

- **Breaking Changes:** None - backward compatible with existing Windows installations
- **Dependencies:** No new external dependencies (stdlib only)
- **Python Version:** Still requires Python 3.10+

### 🐛 Bug Fixes

- Fixed OneDrive Desktop redirect detection on Windows (issue reported via GitHub)
- Fixed hardcoded `LOCALAPPDATA` path assumptions
- Fixed `.bat` extension hardcoded references

### 📈 Metrics

- **Lines Added:** ~600
- **Lines Modified:** ~50
- **Files Created:** 6
- **Files Modified:** 5
- **Tests Added:** 31
- **Platforms Supported:** 1 → 3

---

## [0.3.5] - Previous Version

- Windows-only release
- Initial MCP Vault implementation
- Basic booster injection and config hijacking
