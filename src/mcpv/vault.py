import json
import sys
import shutil
import os
from pathlib import Path
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

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
CONFIG_DIR = HOME_DIR / ".gemini" / "antigravity"
CONFIG_FILE = CONFIG_DIR / "mcp_config.json"
BACKUP_FILE = CONFIG_DIR / "mcp_config.original.json"
ROOT_PATH_FILE = CONFIG_DIR / "root_path.txt"
MY_SERVER_NAME = "mcpv-proxy"

# 안티그래비티 경로
ANTIGRAVITY_PATH = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Antigravity"
ANTIGRAVITY_EXE = ANTIGRAVITY_PATH / "Antigravity.exe"
BOOSTER_SCRIPT = CONFIG_DIR / "boost_launcher.bat"

class VaultManager:
    def __init__(self):
        self.stack = AsyncExitStack()
        self.sessions = {}

    def install(self, force: bool = False):
        """1. MCP Config 하이재킹 및 경로 고정"""
        success = self._hijack_config(force)
        if success:
            """2. 부스팅 스크립트 설치"""
            self._install_booster()
            print("✨ Installation & Path Lock Complete!")

    def _hijack_config(self, force: bool) -> bool:
        if not CONFIG_DIR.exists():
            try:
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            except:
                print(f"❌ Config dir creation failed at {CONFIG_DIR}", file=sys.stderr)
                return False

        if not CONFIG_FILE.exists():
             with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": {}}, f)

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: config = json.load(f)
        except:
            config = {"mcpServers": {}}

        servers = config.get("mcpServers", {})
        other_servers = {k: v for k, v in servers.items() if k != MY_SERVER_NAME}

        if other_servers and not force:
            print(f"⚠️  Existing MCP servers found: {list(other_servers.keys())}", file=sys.stderr)
            print("   Skipping installation. Use 'mcpv install --force' to override.", file=sys.stderr)
            return False

        if other_servers:
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump({"mcpServers": other_servers}, f, indent=2)
            print(f"📦 Backup created at: {BACKUP_FILE}", file=sys.stderr)

        # [핵심] 현재 경로 저장
        current_python = sys.executable
        current_cwd = os.getcwd()
        
        print(f"🔧 Locking Project Root to: {current_cwd}")
        
        try:
            with open(ROOT_PATH_FILE, "w", encoding="utf-8") as f:
                f.write(current_cwd)
            print(f"📍 Root path saved to {ROOT_PATH_FILE}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Failed to save root path: {e}", file=sys.stderr)

        my_config = {
            "command": current_python,
            "args": ["-m", "mcpv", "start"],
            "cwd": current_cwd,
            "env": {
                "PYTHONUNBUFFERED": "1",
                "PYTHONPATH": current_cwd
            }
        }
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"mcpServers": {MY_SERVER_NAME: my_config}}, f, indent=2)
            
        print(f"🔒 Vault config updated.", file=sys.stderr)
        return True

    def _install_booster(self):
        print("🚀 Installing Booster Script...", file=sys.stderr)
        if not ANTIGRAVITY_PATH.exists():
             print(f"⚠️  Antigravity path not found. Skipping booster.", file=sys.stderr)
             return

        batch_content = f"""@echo off
set __COMPAT_LAYER=RunAsInvoker
cd /d "{ANTIGRAVITY_PATH}"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 26646 -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; $env:Path = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0;' + [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User'); Start-Process -FilePath '.\\Antigravity.exe' -ArgumentList '--disable-gpu-driver-bug-workarounds --ignore-gpu-blacklist --enable-gpu-rasterization --enable-zero-copy --enable-native-gpu-memory-buffers' -WorkingDirectory '{ANTIGRAVITY_PATH}'"
exit
"""
        try:
            with open(BOOSTER_SCRIPT, "w", encoding="utf-8") as f:
                f.write(batch_content)
            self._create_shortcut_vbs(str(BOOSTER_SCRIPT), "Antigravity Boost (mcpv)", str(ANTIGRAVITY_EXE))
        except Exception as e:
            print(f"⚠️  Booster installation failed: {e}", file=sys.stderr)

    def _create_shortcut_vbs(self, target, name, icon):
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        link_path = desktop / f"{name}.lnk"
        vbs_script = f'''
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{link_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "cmd.exe"
            oLink.Arguments = "/c ""{target}"""
            oLink.IconLocation = "{icon},0"
            oLink.WindowStyle = 7 
            oLink.Save
        '''
        vbs_file = CONFIG_DIR / "create_shortcut.vbs"
        try:
            with open(vbs_file, "w", encoding="utf-8") as f: f.write(vbs_script)
            os.system(f"cscript //nologo {vbs_file}")
        finally:
            if vbs_file.exists(): os.remove(vbs_file)

    async def get_session(self, server_name):
        if server_name in self.sessions: return self.sessions[server_name]
        if not BACKUP_FILE.exists(): raise FileNotFoundError("Vault is empty.")
        with open(BACKUP_FILE, "r") as f: config = json.load(f)
        srv = config["mcpServers"].get(server_name)
        if not srv: raise ValueError(f"Server {server_name} not found.")
        
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
        
        read, write = await self.stack.enter_async_context(stdio_client(params))
        session = await self.stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.sessions[server_name] = session
        return session

    async def cleanup(self):
        await self.stack.aclose()

manager = VaultManager()