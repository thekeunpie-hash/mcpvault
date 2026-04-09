"""
Cross-platform utility module for creating desktop shortcuts and launchers.

Handles:
- Windows: OneDrive Desktop redirect detection, .lnk shortcuts via PowerShell
- macOS: Applications folder, .command files
- Linux: XDG desktop directories, .desktop files
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional


def get_desktop_path() -> Path:
    """
    Get the actual Desktop directory path for the current platform.
    
    Handles:
    - Windows OneDrive Desktop redirect via registry
    - macOS ~/Desktop
    - Linux XDG Desktop directory
    """
    system = platform.system()
    
    if system == "Windows":
        return _get_windows_desktop()
    elif system == "Darwin":
        return Path.home() / "Desktop"
    else:  # Linux and others
        return _get_linux_desktop()


def _get_windows_desktop() -> Path:
    """
    Get Windows Desktop path, handling OneDrive redirect.
    
    Checks registry key: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders\\Desktop
    Falls back to USERPROFILE\\Desktop if registry query fails.
    """
    try:
        # Query registry for Desktop path (handles OneDrive redirect)
        result = subprocess.run(
            [
                "reg", "query",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
                "/v", "Desktop"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse registry output - look for the path value
            for line in result.stdout.splitlines():
                if "Desktop" in line and "REG" in line:
                    # Extract path from registry output
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        desktop_path = parts[-1]
                        # Expand environment variables like %USERPROFILE%
                        if "%" in desktop_path:
                            desktop_path = os.path.expandvars(desktop_path)
                        return Path(desktop_path)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass
    
    # Fallback to default Desktop location
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        return Path(userprofile) / "Desktop"
    return Path.home() / "Desktop"


def _get_linux_desktop() -> Path:
    """
    Get Linux Desktop path using XDG user directories.
    
    Tries xdg-user-dir first, falls back to ~/Desktop.
    """
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    
    return Path.home() / "Desktop"


def get_applications_path() -> Optional[Path]:
    """
    Get the Applications directory for system menu integration.
    
    Returns:
    - Windows: Start Menu Programs folder
    - macOS: ~/Applications or /Applications
    - Linux: ~/.local/share/applications
    """
    system = platform.system()
    
    if system == "Windows":
        return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    elif system == "Darwin":
        apps = Path.home() / "Applications"
        if not apps.exists():
            apps = Path("/Applications")
        return apps
    else:  # Linux
        return Path.home() / ".local" / "share" / "applications"


def create_launcher(
    name: str,
    target: str,
    icon: Optional[str] = None,
    hidden_window: bool = False,
    arguments: Optional[str] = None
) -> Path:
    """
    Create a platform-appropriate launcher/shortcut.
    
    Args:
        name: Name of the launcher (without extension)
        target: Target executable or script path
        icon: Optional icon path
        hidden_window: If True, launch with minimized/hidden window
        arguments: Optional command-line arguments for the target
    
    Returns:
        Path to the created launcher file
    
    Raises:
        OSError: If launcher creation fails on the current platform
    """
    system = platform.system()
    
    if system == "Windows":
        return _create_windows_shortcut(name, target, icon, hidden_window, arguments)
    elif system == "Darwin":
        return _create_macos_launcher(name, target, icon, hidden_window, arguments)
    else:  # Linux and others
        return _create_linux_desktop_file(name, target, icon, hidden_window, arguments)


def _create_windows_shortcut(
    name: str,
    target: str,
    icon: Optional[str],
    hidden_window: bool,
    arguments: Optional[str]
) -> Path:
    """
    Create Windows .lnk shortcut using PowerShell.
    
    Handles OneDrive Desktop redirect automatically via get_desktop_path().
    """
    desktop = get_desktop_path()
    link_path = desktop / f"{name}.lnk"
    
    # Ensure Desktop directory exists
    desktop.mkdir(parents=True, exist_ok=True)
    
    # Build PowerShell command
    window_style = 7 if hidden_window else 1  # 7 = Minimized, 1 = Normal
    
    def escape_ps_string(s: str) -> str:
        """Escape string for safe PowerShell double-quoted string."""
        if not s:
            return ""
        # Order matters: backtick first, then special chars
        replacements = [
            ('`', '``'), ('"', '`"'), ('$', '`$'),
            ('(', '`('), (')', '`)'), ('[', '`['), (']', '`]'),
            ('{', '`{'), ('}', '`}'), ('|', '`|'), ('&', '`&'),
            (';', '`;'), ('<', '`<'), ('>', '`>'), ('\n', '`n'),
            ('\r', '`r'), ('\t', '`t')
        ]
        for old, new in replacements:
            s = s.replace(old, new)
        return s
    
    target_escaped = escape_ps_string(target)
    icon_escaped = escape_ps_string(icon or "")
    link_path_escaped = escape_ps_string(str(link_path))
    
    if arguments:
        args_escaped = escape_ps_string(arguments)
        args_part = f'; $s.Arguments = "{args_escaped}"'
    else:
        args_part = ""
    
    icon_part = f'; $s.IconLocation = "{icon_escaped},0"' if icon else ""
    
    ps_command = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{link_path_escaped}"); '
        f'$s.TargetPath = "{target_escaped}"; '
        f'{args_part}'
        f'{icon_part}'
        f'; $s.WindowStyle = {window_style}; '
        f'$s.Save()'
    )
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise OSError(f"PowerShell failed: {result.stderr}")
        
        if not link_path.exists():
            raise OSError("Shortcut file was not created")
        
        return link_path
        
    except subprocess.TimeoutExpired:
        raise OSError("PowerShell command timed out")
    except subprocess.SubprocessError as e:
        raise OSError(f"Failed to create shortcut: {e}")


def _create_macos_launcher(
    name: str,
    target: str,
    icon: Optional[str],
    hidden_window: bool,
    arguments: Optional[str]
) -> Path:
    """
    Create macOS launcher as .command file or .app bundle.
    
    For simplicity, creates a .command file in ~/Applications or Desktop.
    """
    # Try Applications folder first, fallback to Desktop
    apps_dir = get_applications_path()
    if apps_dir and apps_dir.exists():
        launcher_dir = apps_dir
    else:
        launcher_dir = get_desktop_path()
    
    launcher_dir.mkdir(parents=True, exist_ok=True)
    launcher_path = launcher_dir / f"{name}.command"
    
    # Build script content
    script_content = f'#!/bin/bash\n'
    
    if hidden_window:
        script_content += '# Launch hidden (background)\n'
    
    if arguments:
        script_content += f'"{target}" {arguments}\n'
    else:
        script_content += f'"{target}"\n'
    
    try:
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(launcher_path, 0o755)
        
        return launcher_path
        
    except OSError as e:
        raise OSError(f"Failed to create macOS launcher: {e}")


def _create_linux_desktop_file(
    name: str,
    target: str,
    icon: Optional[str],
    hidden_window: bool,
    arguments: Optional[str]
) -> Path:
    """
    Create Linux .desktop file (XDG standard).
    
    Creates in XDG Desktop directory for desktop visibility.
    """
    desktop_dir = get_desktop_path()
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = desktop_dir / f"{name}.desktop"
    
    def escape_desktop_value(s: str) -> str:
        """Escape value for .desktop file per XDG spec."""
        if not s:
            return ""
        # Escape special characters for Exec key per XDG Desktop Entry spec
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('`', '\\`')
        s = s.replace('$', '\\$')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return s
    
    name_escaped = escape_desktop_value(name)
    target_escaped = escape_desktop_value(target)
    args_escaped = escape_desktop_value(arguments or "")
    icon_escaped = escape_desktop_value(icon or "")
    
    # Build .desktop file content
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={name_escaped}
Exec={target_escaped} {args_escaped}
"""
    
    if icon:
        desktop_content += f"Icon={icon_escaped}\n"
    
    if hidden_window:
        desktop_content += "StartupNotify=false\n"
    
    desktop_content += "Terminal=false\n"
    
    try:
        with open(desktop_path, "w", encoding="utf-8") as f:
            f.write(desktop_content)
        
        # Make executable
        os.chmod(desktop_path, 0o755)
        
        return desktop_path
        
    except OSError as e:
        raise OSError(f"Failed to create .desktop file: {e}")
