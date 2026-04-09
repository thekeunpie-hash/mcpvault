"""
Platform abstraction layer for cross-platform support.

Handles OS-specific paths, executables, process management, and system commands.
This module centralizes all platform-specific logic for MCP Vault.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


class PlatformInfo:
    """Provides platform-specific information and utilities."""
    
    def __init__(self):
        self._platform = sys.platform
        self._is_windows = self._platform.startswith("win")
        self._is_macos = self._platform == "darwin"
        self._is_linux = self._platform.startswith("linux")
    
    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self._is_windows
    
    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self._is_macos
    
    @property
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self._is_linux
    
    @property
    def platform_name(self) -> str:
        """Get human-readable platform name."""
        if self.is_windows:
            return "Windows"
        elif self.is_macos:
            return "macOS"
        elif self.is_linux:
            return "Linux"
        return "Unknown"
    
    def get_appdata_path(self) -> Path:
        """
        Get platform-specific application data directory.
        
        Windows: LOCALAPPDATA/Antigravity
        macOS: ~/Library/Application Support/Antigravity
        Linux: ~/.local/share/antigravity (or XDG_DATA_HOME)
        """
        if self.is_windows:
            appdata = os.environ.get("LOCALAPPDATA", "")
            if appdata:
                return Path(appdata) / "Antigravity"
            return Path.home() / "AppData" / "Local" / "Antigravity"
        elif self.is_macos:
            return Path.home() / "Library" / "Application Support" / "Antigravity"
        else:  # Linux
            xdg_data = os.environ.get("XDG_DATA_HOME", "")
            if xdg_data:
                return Path(xdg_data) / "antigravity"
            return Path.home() / ".local" / "share" / "antigravity"
    
    def get_config_dir(self) -> Path:
        """
        Get platform-specific configuration directory.
        
        All platforms: ~/.gemini/antigravity (for MCP config compatibility)
        """
        return Path.home() / ".gemini" / "antigravity"
    
    def get_executable_name(self, base_name: str) -> str:
        """
        Add platform-specific executable extension.
        
        Windows: adds .exe if not present
        macOS/Linux: no extension
        """
        if self.is_windows:
            if not base_name.endswith(".exe"):
                return f"{base_name}.exe"
            return base_name
        return base_name
    
    def get_script_extension(self) -> str:
        """
        Get platform-specific script extension.
        
        Windows: .bat
        macOS/Linux: .sh
        """
        return ".bat" if self.is_windows else ".sh"
    
    def get_shell_command(self) -> list:
        """
        Get platform-specific shell command for running scripts.
        
        Windows: cmd.exe /c
        macOS/Linux: /bin/bash -c
        """
        if self.is_windows:
            return ["cmd.exe", "/c"]
        return ["/bin/bash", "-c"]
    
    def get_process_kwargs(self) -> Dict[str, Any]:
        """
        Get platform-specific subprocess kwargs.
        
        Windows: CREATE_NO_WINDOW flag to hide console
        macOS/Linux: No special flags needed
        """
        if self.is_windows:
            try:
                import subprocess
                return {"creationflags": subprocess.CREATE_NO_WINDOW}
            except (ImportError, AttributeError):
                pass
        return {}
    
    def get_antigravity_exe_path(self) -> Path:
        """
        Get platform-specific Antigravity executable path.
        
        Windows: LOCALAPPDATA/Programs/Antigravity/Antigravity.exe
        macOS: /Applications/Antigravity.app/Contents/MacOS/Antigravity
        Linux: ~/.local/bin/antigravity or /usr/bin/antigravity
        """
        if self.is_windows:
            appdata = os.environ.get("LOCALAPPDATA", "")
            if appdata:
                return Path(appdata) / "Programs" / "Antigravity" / "Antigravity.exe"
            return Path.home() / "AppData" / "Local" / "Programs" / "Antigravity" / "Antigravity.exe"
        elif self.is_macos:
            return Path("/Applications/Antigravity.app/Contents/MacOS/Antigravity")
        else:  # Linux
            # Check common Linux installation paths
            local_bin = Path.home() / ".local" / "bin" / "antigravity"
            if local_bin.exists():
                return local_bin
            return Path("/usr/bin/antigravity")
    
    def get_booster_script_name(self) -> str:
        """
        Get platform-specific booster script name.
        
        Windows: boost_launcher.bat
        macOS/Linux: boost_launcher.sh
        """
        return f"boost_launcher{self.get_script_extension()}"
    
    def get_desktop_path(self) -> Path:
        """
        Get platform-specific Desktop directory.
        
        Delegates to platform_utils for implementation.
        """
        # Import here to avoid circular dependency
        from . import platform_utils
        return platform_utils.get_desktop_path()
    
    def get_applications_path(self) -> Optional[Path]:
        """
        Get platform-specific Applications/Programs directory for menu integration.
        
        Windows: Start Menu/Programs
        macOS: ~/Applications or /Applications
        Linux: ~/.local/share/applications
        """
        if self.is_windows:
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        elif self.is_macos:
            apps = Path.home() / "Applications"
            if not apps.exists():
                apps = Path("/Applications")
            return apps
        else:  # Linux
            return Path.home() / ".local" / "share" / "applications"
    
    def run_shell_command(self, command: str, capture: bool = False) -> subprocess.CompletedProcess:
        """
        Run a shell command with platform-specific settings.
        
        SECURITY: Uses shell=False with argument list to prevent shell injection.
        Dangerous shell metacharacters are blocked: |, &, ;, `, $, (), <>, {}
        
        Args:
            command: Command string to execute
            capture: If True, capture stdout and stderr
        
        Returns:
            CompletedProcess instance with returncode, stdout, stderr
        
        Raises:
            ValueError: If command contains dangerous shell metacharacters
        """
        # Security check: block dangerous shell metacharacters
        dangerous_chars = ['|', '&', ';', '`', '$', '(', ')', '{', '}', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in command:
                raise ValueError(f"⛔ Security: Dangerous character '{char}' not allowed in command")
        
        kwargs = self.get_process_kwargs()
        if capture:
            kwargs["capture_output"] = True
            kwargs["text"] = True
        
        # Use shell=False for security - pass command as argument list
        shell_cmd = self.get_shell_command()
        full_command = shell_cmd + [command]
        
        return subprocess.run(full_command, **kwargs)


# Global instance for easy access
platform_info = PlatformInfo()


def get_platform_info() -> PlatformInfo:
    """Get the global PlatformInfo instance."""
    return platform_info
