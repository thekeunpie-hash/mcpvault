import os
import json
import subprocess
import logging
import sys
from pathlib import Path
from fastmcp import FastMCP
from .valve import valve
from .vault import manager

# 1. 로깅 및 설정 폴더
CONFIG_DIR = Path.home() / ".gemini" / "antigravity"
LOG_DIR = CONFIG_DIR
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except:
    pass

LOG_FILE = LOG_DIR / "mcpv_debug.log"
ROOT_PATH_FILE = CONFIG_DIR / "root_path.txt"

# 기존 핸들러 제거
root_logger = logging.getLogger()
if root_logger.handlers:
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    encoding="utf-8",
    force=True
)
logger = logging.getLogger("mcpv-server")

# 2. 실행 위치 감지 및 [중요] CWD 변경
if ROOT_PATH_FILE.exists():
    try:
        content = ROOT_PATH_FILE.read_text(encoding="utf-8").strip()
        ROOT_DIR = Path(content).resolve()
        source = "FILE(root_path.txt)"
        
        # [핵심 수정] 프로세스의 작업 디렉토리를 강제로 변경
        os.chdir(ROOT_DIR)
        logger.info(f"✅ Changed CWD to: {os.getcwd()}")
        
    except Exception as e:
        ROOT_DIR = Path.cwd().resolve()
        source = f"CWD(File Read Error: {e})"
else:
    ROOT_DIR = Path.cwd().resolve()
    source = "CWD(File Not Found)"

logger.info("="*40)
logger.info(f"🚀 MCPV Server Started.")
logger.info(f"📂 Project Root: {ROOT_DIR} (Source: {source})")
logger.info(f"📂 Current Work Dir: {os.getcwd()}")
logger.info("="*40)

IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".md", ".json", ".txt", ".html", ".css", ".java", ".c", ".cpp", ".rs", ".go"}

mcp = FastMCP("mcpv", log_level="DEBUG")

@mcp.tool()
def get_vault_info() -> str:
    """
    [System Discovery] Returns a list of available upstream MCP servers in the Vault.
    You MUST use these 'server_name's when calling 'use_upstream_tool'.
    """
    from .vault import BACKUP_FILE
    
    if not BACKUP_FILE.exists():
        return "Vault is empty. No upstream servers configured."
        
    try:
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        servers = config.get("mcpServers", {})
        if not servers:
            return "Vault config exists but no servers found."
            
        report = ["=== 🛡️ Available MCP Servers in Vault ==="]
        for name, cfg in servers.items():
            status = "DISABLED" if cfg.get("disabled", False) else "ACTIVE"
            cmd = cfg.get("command", "unknown")
            report.append(f"- Server ID: '{name}' ({status})")
            report.append(f"  Command: {cmd}")
            
        report.append("\n[Instruction]")
        report.append("To use tools from these servers, use:")
        report.append("use_upstream_tool(server_name='Server ID', tool_name='Tool Name', args={...})")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Error reading vault info: {str(e)}"


@mcp.tool()
def get_initial_context(force: bool = False) -> str:
    """[Smart Valve] Loads the codebase context via Repomix."""
    logger.info(f"Function 'get_initial_context' called. force={force}")
    
    allowed, msg = valve.check(force)
    logger.info(f"Valve check result: allowed={allowed}")
    
    if not allowed:
        return msg

    # 2. [Added] Get MCP Server Info
    # ---------------------------------------------------------
    vault_info = "=== MCP Servers ===\nNo servers found."
    try:
        from .vault import BACKUP_FILE
        if BACKUP_FILE.exists():
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                srvs = json.load(f).get("mcpServers", {})
                active_srvs = [k for k, v in srvs.items() if not v.get("disabled")]
                vault_info = f"=== 🛡️ Active MCP Servers ===\n" + "\n".join([f"- {s}" for s in active_srvs])
                vault_info += "\n(Use these names for 'use_upstream_tool')"
    except:
        pass
    # ---------------------------------------------------------

    try:
        # CWD가 이미 변경되었으므로 명령어만 실행하면 됨
        cmd = [
            "npx", "-y", "repomix",
            "--style", "xml",
            "--compress",
            "--remove-comments",
            "--output", "stdout"
        ]
        
        logger.info(f"▶️ Executing command: {' '.join(cmd)}")
        logger.info(f"   in Directory: {os.getcwd()}") # ROOT_DIR과 동일해야 함
        
        env = os.environ.copy()
        env["CI"] = "true"
        
        result = subprocess.run(
            cmd,
            cwd=ROOT_DIR, # 명시적으로 한 번 더 지정
            capture_output=True,
            text=True,
            encoding="utf-8",
            shell=(os.name == 'nt'),
            timeout=120,
            env=env,
            stdin=subprocess.DEVNULL 
        )
        
        if result.returncode != 0:
            err_msg = f"Repomix Error (Code {result.returncode}): {result.stderr}"
            logger.error(err_msg)
            return err_msg
            
        output_len = len(result.stdout)
        logger.info(f"📝 Context fetched successfully! Length: {output_len} chars")

        output = result.stdout
        
        # [Modified] Combine Vault Info
        final_output = f"{vault_info}\n\n=== 📂 Project Context ===\n{output}\n=== End Vault ==="
        
        # Cache update
        valve.update_cache(ROOT_DIR, final_output)
        
        return final_output
        
    except subprocess.TimeoutExpired:
        logger.error("⏰ Repomix timed out.")
        return "Error: Context fetching timed out."
    except Exception as e:
        logger.exception("❌ Unexpected error")
        return f"Vault Error: {str(e)}"

@mcp.tool()
async def use_upstream_tool(server_name: str, tool_name: str, args: dict = {}) -> str:
    """Routes a command to a specific server in the vault."""
    try:
        # upstream 서버들도 이제 변경된 CWD(프로젝트 루트)에서 실행됩니다.
        session = await manager.get_session(server_name)
        res = await session.call_tool(tool_name, args)
        return "\n".join([c.text for c in res.content if c.type == "text"])
    except Exception as e:
        logger.error(f"Gateway Error: {e}")
        return f"Gateway Error: {e}"

@mcp.tool()
def list_directory(path: str = ".") -> str:
    logger.debug(f"list_directory called: {path}")
    full = (ROOT_DIR / path).resolve()
    if not str(full).startswith(str(ROOT_DIR)): return "⛔ Access Denied"
    if not full.exists(): return "Not found"
    
    out = []
    try:
        with os.scandir(full) as it:
            for e in it:
                if e.name in IGNORE_DIRS or e.name.startswith("."): continue
                if e.is_dir(): out.append(f"[DIR]  {e.name}/")
                elif e.is_file() and Path(e.name).suffix in ALLOWED_EXTENSIONS: out.append(f"[FILE] {e.name}")
    except Exception as e:
        return str(e)
    return "\n".join(sorted(out)) if out else "Empty"

@mcp.tool()
def read_file(path: str) -> str:
    logger.debug(f"read_file called: {path}")
    full = (ROOT_DIR / path).resolve()
    if not str(full).startswith(str(ROOT_DIR)): return "⛔ Access Denied"
    if full.suffix not in ALLOWED_EXTENSIONS: return f"⛔ File type {full.suffix} not allowed"
    try: return full.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return str(e)
