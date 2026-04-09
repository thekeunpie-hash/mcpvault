"""
Unit tests for platform_abstraction module.

Tests cover:
- Platform detection
- Path resolution for each platform
- Executable naming conventions
- Script extensions
- Shell command generation
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcpv.platform_abstraction import PlatformInfo, platform_info, get_platform_info


class TestPlatformInfo(unittest.TestCase):
    """Test cases for PlatformInfo class."""

    def setUp(self):
        """Set up test fixtures."""
        self.platform = PlatformInfo()

    def test_platform_detection(self):
        """Test platform detection properties."""
        # One of these should be True based on the running system
        is_one_platform = (
            self.platform.is_windows or 
            self.platform.is_macos or 
            self.platform.is_linux
        )
        self.assertTrue(is_one_platform, "Should detect at least one platform")
        
        # Platform name should be non-empty
        self.assertTrue(len(self.platform.platform_name) > 0)

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    def test_windows_platform_detection(self):
        """Test Windows platform detection."""
        platform = PlatformInfo()
        self.assertTrue(platform.is_windows)
        self.assertFalse(platform.is_macos)
        self.assertFalse(platform.is_linux)
        self.assertEqual(platform.platform_name, "Windows")

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    def test_macos_platform_detection(self):
        """Test macOS platform detection."""
        platform = PlatformInfo()
        self.assertFalse(platform.is_windows)
        self.assertTrue(platform.is_macos)
        self.assertFalse(platform.is_linux)
        self.assertEqual(platform.platform_name, "macOS")

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    def test_linux_platform_detection(self):
        """Test Linux platform detection."""
        platform = PlatformInfo()
        self.assertFalse(platform.is_windows)
        self.assertFalse(platform.is_macos)
        self.assertTrue(platform.is_linux)
        self.assertEqual(platform.platform_name, "Linux")

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    @patch.dict(os.environ, {'LOCALAPPDATA': 'C:\\Users\\Test\\AppData\\Local'})
    def test_windows_appdata_path(self):
        """Test Windows appdata path resolution."""
        platform = PlatformInfo()
        path = platform.get_appdata_path()
        self.assertIn("Antigravity", str(path))
        self.assertTrue(str(path).startswith("C:\\Users\\Test"))

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    @patch.object(Path, 'home', return_value=Path('/Users/test'))
    def test_macos_appdata_path(self, mock_home):
        """Test macOS appdata path resolution."""
        platform = PlatformInfo()
        path = platform.get_appdata_path()
        self.assertEqual(
            path, 
            Path('/Users/test/Library/Application Support/Antigravity')
        )

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    @patch.object(Path, 'home', return_value=Path('/home/test'))
    def test_linux_appdata_path(self, mock_home):
        """Test Linux appdata path resolution."""
        platform = PlatformInfo()
        path = platform.get_appdata_path()
        self.assertEqual(
            path, 
            Path('/home/test/.local/share/antigravity')
        )

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    def test_windows_executable_name(self):
        """Test Windows executable naming."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_executable_name("app"), "app.exe")
        self.assertEqual(platform.get_executable_name("app.exe"), "app.exe")
        self.assertEqual(platform.get_executable_name("my-app"), "my-app.exe")

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    def test_macos_executable_name(self):
        """Test macOS executable naming."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_executable_name("app"), "app")
        self.assertEqual(platform.get_executable_name("app.exe"), "app.exe")

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    def test_linux_executable_name(self):
        """Test Linux executable naming."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_executable_name("app"), "app")
        self.assertEqual(platform.get_executable_name("app.exe"), "app.exe")

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    def test_windows_script_extension(self):
        """Test Windows script extension."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_script_extension(), ".bat")

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    def test_macos_script_extension(self):
        """Test macOS script extension."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_script_extension(), ".sh")

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    def test_linux_script_extension(self):
        """Test Linux script extension."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_script_extension(), ".sh")

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    def test_windows_shell_command(self):
        """Test Windows shell command."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_shell_command(), ["cmd.exe", "/c"])

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    def test_macos_shell_command(self):
        """Test macOS shell command."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_shell_command(), ["/bin/bash", "-c"])

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    def test_linux_shell_command(self):
        """Test Linux shell command."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_shell_command(), ["/bin/bash", "-c"])

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    def test_windows_process_kwargs(self):
        """Test Windows process kwargs."""
        platform = PlatformInfo()
        kwargs = platform.get_process_kwargs()
        # On Windows, should have creationflags
        if hasattr(platform, '_subprocess_module'):
            self.assertIn("creationflags", kwargs)

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    def test_macos_process_kwargs(self):
        """Test macOS process kwargs."""
        platform = PlatformInfo()
        kwargs = platform.get_process_kwargs()
        self.assertEqual(kwargs, {})

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    def test_linux_process_kwargs(self):
        """Test Linux process kwargs."""
        platform = PlatformInfo()
        kwargs = platform.get_process_kwargs()
        self.assertEqual(kwargs, {})

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    @patch.dict(os.environ, {'LOCALAPPDATA': 'C:\\Users\\Test\\AppData\\Local'})
    def test_windows_antigravity_exe_path(self):
        """Test Windows Antigravity executable path."""
        platform = PlatformInfo()
        path = platform.get_antigravity_exe_path()
        self.assertIn("Antigravity.exe", str(path))
        self.assertIn("Programs", str(path))

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    def test_macos_antigravity_exe_path(self):
        """Test macOS Antigravity executable path."""
        platform = PlatformInfo()
        path = platform.get_antigravity_exe_path()
        self.assertIn("Antigravity.app", str(path))
        # Use os.sep for cross-platform path separator check
        self.assertTrue("Contents" in str(path) and "MacOS" in str(path))

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    def test_linux_antigravity_exe_path(self):
        """Test Linux Antigravity executable path."""
        platform = PlatformInfo()
        path = platform.get_antigravity_exe_path()
        # Should be either ~/.local/bin/antigravity or /usr/bin/antigravity
        self.assertTrue(
            str(path).endswith("antigravity")
        )

    @patch('mcpv.platform_abstraction.sys.platform', 'win32')
    def test_windows_booster_script_name(self):
        """Test Windows booster script name."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_booster_script_name(), "boost_launcher.bat")

    @patch('mcpv.platform_abstraction.sys.platform', 'darwin')
    def test_macos_booster_script_name(self):
        """Test macOS booster script name."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_booster_script_name(), "boost_launcher.sh")

    @patch('mcpv.platform_abstraction.sys.platform', 'linux')
    def test_linux_booster_script_name(self):
        """Test Linux booster script name."""
        platform = PlatformInfo()
        self.assertEqual(platform.get_booster_script_name(), "boost_launcher.sh")

    def test_config_dir(self):
        """Test config directory is consistent across platforms."""
        # Config dir should always be ~/.gemini/antigravity
        config_dir = self.platform.get_config_dir()
        self.assertIn(".gemini", str(config_dir))
        self.assertIn("antigravity", str(config_dir))

    def test_global_instance(self):
        """Test global platform_info instance."""
        self.assertIsInstance(platform_info, PlatformInfo)
        
    def test_get_platform_info(self):
        """Test get_platform_info function."""
        info = get_platform_info()
        self.assertIsInstance(info, PlatformInfo)
        self.assertIs(info, platform_info)  # Should return same instance


class TestPlatformIntegration(unittest.TestCase):
    """Integration tests for platform_abstraction with actual system."""

    def test_actual_platform_detection(self):
        """Test that platform detection works on actual system."""
        info = get_platform_info()
        
        # Verify at least one platform flag is set
        platforms = [info.is_windows, info.is_macos, info.is_linux]
        self.assertEqual(sum(platforms), 1, "Exactly one platform should be detected")

    def test_actual_paths_exist(self):
        """Test that generated paths are valid Path objects."""
        info = get_platform_info()
        
        # All path methods should return Path objects
        self.assertIsInstance(info.get_appdata_path(), Path)
        self.assertIsInstance(info.get_config_dir(), Path)
        self.assertIsInstance(info.get_antigravity_exe_path(), Path)
        self.assertIsInstance(info.get_desktop_path(), Path)

    def test_actual_shell_command(self):
        """Test that shell command returns valid list."""
        info = get_platform_info()
        cmd = info.get_shell_command()
        self.assertIsInstance(cmd, list)
        self.assertEqual(len(cmd), 2)


if __name__ == "__main__":
    unittest.main()
