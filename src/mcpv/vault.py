import json
import sys
import shutil
import os
import subprocess
import asyncio
from pathlib import Path
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from . import platform_utils
from .platform_abstraction import platform_info

# === Timeout Constants (REQ-02, REQ-05) ===
CONNECTION_TIMEOUT = 15.0  # Timeout for session establishment

# [Import 호환성 처리]
try:
    from mcp.types import StdioServerParameters
except ImportError:
    try:
        from mcp import StdioServerParameters
    except ImportError:
        from typing import Any
        StdioServerParameters = Any

# 경로 설정
HOME_DIR = Path.home()
CONFIG_DIR = platform_info.get_config_dir()
CONFIG_FILE = CONFIG_DIR / "mcp_config.json"
BACKUP_FILE = CONFIG_DIR / "mcp_config.original.json"
ROOT_PATH_FILE = CONFIG_DIR / "root_path.txt"
MY_SERVER_NAME = "mcpv-proxy"

# 안티그래비티 경로 (Cross-platform)
ANTIGRAVITY_PATH = platform_info.get_antigravity_exe_path().parent
ANTIGRAVITY_EXE = platform_info.get_antigravity_exe_path()
BOOSTER_SCRIPT = CONFIG_DIR / platform_info.get_booster_script_name()

class VaultManager:
    def __init__(self):
        self.stack = AsyncExitStack()
        self.sessions = {}
        self._session_locks = {}  # Per-server locks
        self._global_lock = asyncio.Lock()
        self._session_stacks = {}  # Store session-specific stacks to keep them alive

    def install(self, force: bool = False):
        """1. MCP Config 하이재킹 및 경로 고정"""
        print("🔧 Starting MCP Vault Installation...")
        try:
            success = self._hijack_config(force)
            if success:
                """2. 부스팅 스크립트 설치"""
                self._install_booster()
                print("\n✅ Installation & Path Lock Complete! You are ready to go.")
            else:
                print("\n⚠️ Installation skipped or failed during config setup.")
        except Exception as e:
            print(f"\n❌ FATAL: Unhandled installation error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    def _hijack_config(self, force: bool) -> bool:
        # [Step 1] Config Directory Check
        if not CONFIG_DIR.exists():
            try:
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                print(f"❌ PERMISSION DENIED: Cannot create config directory at '{CONFIG_DIR}'", file=sys.stderr)
                print("   👉 Try running the command prompt as Administrator.", file=sys.stderr)
                return False
            except Exception as e:
                print(f"❌ ERROR: Failed to create config dir: {e}", file=sys.stderr)
                return False

        # [Step 2] Config File Initialization
        if not CONFIG_FILE.exists():
             try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump({"mcpServers": {}}, f)
             except Exception as e:
                 print(f"❌ ERROR: Failed to initialize empty config file: {e}", file=sys.stderr)
                 return False

        # [Step 3] Read Existing Config
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: config = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  WARNING: Corrupted config file found at '{CONFIG_FILE}'")
            if force:
                print("   👉 --force used. Overwriting corrupted config.")
                config = {"mcpServers": {}}
            else:
                print("   👉 Fix the JSON syntax or use 'mcpv install --force' to reset it.", file=sys.stderr)
                return False
        except Exception as e:
             print(f"❌ ERROR: Failed to read config file: {e}", file=sys.stderr)
             return False

        # [Step 4] Check for Conflicts
        servers = config.get("mcpServers", {})
        other_servers = {k: v for k, v in servers.items() if k != MY_SERVER_NAME}

        if other_servers and not force:
            print(f"\n⚠️  EXISTING MCP SERVERS FOUND: {list(other_servers.keys())}", file=sys.stderr)
            print("   To protect your existing setup, installation paused.", file=sys.stderr)
            print("   👉 Use 'mcpv install --force' to override and backup existing config.", file=sys.stderr)
            return False

        # [Step 5] Backup
        if other_servers:
            try:
                with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                    json.dump({"mcpServers": other_servers}, f, indent=2)
                print(f"📦 Backup created at: {BACKUP_FILE}", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  WARNING: Failed to create backup: {e}", file=sys.stderr)

        # [Step 6] Lock Current Path (Project Root)
        current_python = sys.executable
        current_cwd = os.getcwd()
        
        print(f"📍 Locking Project Root to: {current_cwd}")
        
        try:
            with open(ROOT_PATH_FILE, "w", encoding="utf-8") as f:
                f.write(current_cwd)
        except PermissionError:
             print(f"❌ PERMISSION DENIED: Cannot save root path to '{ROOT_PATH_FILE}'", file=sys.stderr)
             return False
        except Exception as e:
            print(f"❌ ERROR: Failed to save root path: {e}", file=sys.stderr)
            # This is critical, but maybe we can proceed? No, better safe.
            return False

        # [Step 7] Write Final Config
        my_config = {
            "command": current_python,
            "args": ["-m", "mcpv", "start"],
            "cwd": current_cwd,
            "env": {
                "PYTHONUNBUFFERED": "1",
                "PYTHONPATH": current_cwd,
                "PYTHONHOME": sys.prefix
            }
        }
        
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": {MY_SERVER_NAME: my_config}}, f, indent=2)
            print(f"🔒 Vault config updated successfully.", file=sys.stderr)
            return True
        except Exception as e:
            print(f"❌ ERROR: Failed to write final config: {e}", file=sys.stderr)
            return False

    def _install_booster(self):
        print("🚀 Installing Booster Script...", file=sys.stderr)
        
        if not ANTIGRAVITY_PATH.exists():
             print(f"\n⚠️  ANTIGRAVITY NOT FOUND", file=sys.stderr)
             print(f"   Expected path: {ANTIGRAVITY_PATH}", file=sys.stderr)
             print("   👉 Please install the Antigravity application first.", file=sys.stderr)
             return

        batch_content = f"""@echo off
set __COMPAT_LAYER=RunAsInvoker

:: [Admin Check]
net session >nul 2>&1
if %errorLevel% NEQ 0 goto :LAUNCH

echo.
echo ==============================================================================
echo [WARNING] Running as Administrator detected!
echo.
echo Antigravity running as Admin may cause UI glitches (broken drag-drop, etc).
echo It is recommended to run as a Standard User (via Explorer/Shortcut).
echo ==============================================================================
echo.
set /p OPEN_URL="Do you want to check the solution guide? (y/n): "
if /i "%OPEN_URL%"=="y" (
    start https://github.com/thekeunpie-hash/mcpvault
    echo.
    echo Opening guide... Please review the instructions.
    pause
)

:LAUNCH
cd /d "{ANTIGRAVITY_PATH}"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 26646 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; $env:Path = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0;' + [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User'); Start-Process -FilePath '.\\Antigravity.exe' -ArgumentList '--disable-gpu-driver-bug-workarounds --ignore-gpu-blacklist --enable-gpu-rasterization --enable-zero-copy --enable-native-gpu-memory-buffers' -WorkingDirectory '{ANTIGRAVITY_PATH}'"
exit
"""
        try:
            with open(BOOSTER_SCRIPT, "w", encoding="utf-8") as f:
                f.write(batch_content)
            self._create_shortcut(str(BOOSTER_SCRIPT), "Antigravity Boost (mcpv)", str(ANTIGRAVITY_EXE))
            print("   -> Booster script created.", file=sys.stderr)
        except PermissionError:
            print(f"❌ PERMISSION DENIED: Cannot write booster script to '{BOOSTER_SCRIPT}'", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Booster installation failed: {e}", file=sys.stderr)

    def _create_shortcut(self, target, name, icon):
        """Create cross-platform launcher using platform_utils."""
        try:
            # Target is the batch script, icon is the Antigravity executable
            launcher_path = platform_utils.create_launcher(
                name=name,
                target=target,
                icon=icon,
                hidden_window=True
            )
            print(f"   -> Launcher created at: {launcher_path}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Cross-platform launcher creation failed: {e}", file=sys.stderr)
            print("   -> Attempting Windows-only fallback...", file=sys.stderr)
            self._create_shortcut_windows_only(target, name, icon)
    
    def _create_shortcut_windows_only(self, target, name, icon):
        """Fallback Windows-only shortcut creation (legacy behavior)."""
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        link_path = desktop / f"{name}.lnk"
        
        ps_command = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{link_path}"); '
            f'$s.TargetPath = "cmd.exe"; '
            f'$s.Arguments = "/c ""{target}"""; '
            f'$s.IconLocation = "{icon},0"; '
            f'$s.WindowStyle = 7; '
            f'$s.Save()'
        )
        
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_command],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            err_msg = str(e)
            if isinstance(e, subprocess.CalledProcessError) and e.stderr:
                err_msg = e.stderr.decode(errors='replace').strip()
            print(f"⚠️  Windows fallback failed: {err_msg}", file=sys.stderr)




    async def get_session(self, server_name):
        """Get or create session for server. Returns None on timeout (REQ-05)."""
        # Fast path - avoid lock contention for existing sessions
        if server_name in self.sessions:
            return self.sessions[server_name]
        
        # Acquire global lock for session creation coordination
        async with self._global_lock:
            # Double-check after acquiring lock
            if server_name in self.sessions:
                return self.sessions[server_name]
            
            # Create per-server lock if it doesn't exist
            if server_name not in self._session_locks:
                self._session_locks[server_name] = asyncio.Lock()
        
        # Acquire per-server lock for serialized session creation
        async with self._session_locks[server_name]:
            # Triple-check inside per-server lock
            if server_name in self.sessions:
                return self.sessions[server_name]
            
            if not BACKUP_FILE.exists():
                raise FileNotFoundError("Vault is empty.")
            
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            srv = config["mcpServers"].get(server_name)
            if not srv:
                raise ValueError(f"Server {server_name} not found.")
        
        # [수정됨] 상류 서버 실행 시 CI=true 강제 주입
        upstream_env = os.environ.copy()
        upstream_env["CI"] = "true"
        upstream_env.update(srv.get("env", {}))

        # [핵심 수정] Windows에서 npx 등의 명령어 위치 찾기 (npx -> npx.cmd)
        cmd = srv["command"]
        resolved_cmd = shutil.which(cmd)
        
        if not resolved_cmd and os.name == 'nt':
            # .cmd 나 .exe를 붙여서 찾아봄
            resolved_cmd = shutil.which(f"{cmd}.cmd") or shutil.which(f"{cmd}.exe")
        
        # 그래도 못 찾으면 원래 명령어 사용 (PATH에 있다고 가정)
        final_cmd = resolved_cmd if resolved_cmd else cmd

        params = StdioServerParameters(
            command=final_cmd,       # <--- ✅ 수정: Windows 호환 처리가 된 final_cmd 사용
            args=srv.get("args", []),
            env=upstream_env
        )
        
        # REQ-02, REQ-05: Wrap session establishment with timeout
        # Use temporary stack to prevent resource leak on partial failure
        temp_stack = AsyncExitStack()
        try:
            # Establish connection with timeout
            read, write = await asyncio.wait_for(
                temp_stack.enter_async_context(stdio_client(params)),
                timeout=CONNECTION_TIMEOUT
            )
            session = await asyncio.wait_for(
                temp_stack.enter_async_context(ClientSession(read, write)),
                timeout=CONNECTION_TIMEOUT
            )
            await asyncio.wait_for(session.initialize(), timeout=CONNECTION_TIMEOUT)
            
            # Success: store temp_stack to keep resources alive
            # This avoids manipulating private _exit_callbacks attribute
            self._session_stacks[server_name] = temp_stack
            
            self.sessions[server_name] = session
            return session
        except asyncio.TimeoutError:
            # Graceful degradation: cleanup and return None
            await temp_stack.aclose()  # Clean up any partial resources
            print(f"⚠️ Timeout ({CONNECTION_TIMEOUT}s) connecting to {server_name}", file=sys.stderr)
            return None
        except Exception as e:
            # Cleanup on any failure
            await temp_stack.aclose()
            print(f"⚠️ Error connecting to {server_name}: {e}", file=sys.stderr)
            return None

    async def cleanup(self):
        await self.stack.aclose()

    def update_config(self, server_name: str, key: str, value: bool) -> bool:
        """Updates a specific boolean key in the mcp_config.original.json (BACKUP_FILE)."""
        if not BACKUP_FILE.exists():
            return False
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            if server_name not in config.get("mcpServers", {}):
                return False
            
            config["mcpServers"][server_name][key] = value
            
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Failed to update config: {e}", file=sys.stderr)
            return False

    def update_disabled_tools(self, server_name: str, tool_name: str, disabled: bool) -> bool:
        """Updates the disabledTools list for a specific server."""
        if not BACKUP_FILE.exists():
            return False
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            srv = config.get("mcpServers", {}).get(server_name)
            if not srv:
                return False
            
            disabled_list = srv.get("disabledTools", [])
            if disabled:
                if tool_name not in disabled_list:
                    disabled_list.append(tool_name)
            else:
                disabled_list = [t for t in disabled_list if t != tool_name]
            
            srv["disabledTools"] = disabled_list
            
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Failed to update disabled tools: {e}", file=sys.stderr)
            return False

manager = VaultManager()