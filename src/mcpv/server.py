import os
import subprocess
from pathlib import Path
from fastmcp import FastMCP
from .valve import valve
from .vault import manager

# 실행 위치를 동적으로 감지
ROOT_DIR = Path.cwd()
IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".md", ".json", ".txt", ".html", ".css", ".java", ".c", ".cpp", ".rs", ".go"}

mcp = FastMCP("mcpv", log_level="ERROR")

@mcp.tool()
def get_initial_context(force: bool = False) -> str:
    """[Smart Valve] Loads the codebase context via Repomix. Blocks redundant calls."""
    allowed, msg = valve.check(force)
    if not allowed:
        return msg

    try:
        # Repomix 호출
        cmd = ["npx", "-y", "repomix", "--style", "xml", "--compress", "--remove-comments", "--output", "stdout"]
        result = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, encoding="utf-8", shell=(os.name=='nt'))
        if result.returncode != 0: return f"Error: {result.stderr}"
        return f"=== Vault Context ===\n{result.stdout}\n=== End Vault ==="
    except Exception as e:
        return f"Vault Error: {str(e)}"

@mcp.tool()
async def use_upstream_tool(server_name: str, tool_name: str, args: dict = {}) -> str:
    """Routes a command to a specific server in the vault."""
    try:
        session = await manager.get_session(server_name)
        res = await session.call_tool(tool_name, args)
        return "\n".join([c.text for c in res.content if c.type == "text"])
    except Exception as e:
        return f"Gateway Error: {e}"

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """Secure, Lazy file listing."""
    full = (ROOT_DIR / path).resolve()
    if not str(full).startswith(str(ROOT_DIR)): return "⛔ Access Denied (Jailbreak attempt)"
    if not full.exists(): return "Not found"
    
    out = []
    try:
        with os.scandir(full) as it:
            for e in it:
                if e.name in IGNORE_DIRS or e.name.startswith("."): continue
                if e.is_dir(): out.append(f"[DIR]  {e.name}/")
                elif e.is_file() and Path(e.name).suffix in ALLOWED_EXTENSIONS: out.append(f"[FILE] {e.name}")
    except Exception as e: return str(e)
    return "\n".join(sorted(out)) if out else "Empty"

@mcp.tool()
def read_file(path: str) -> str:
    """Secure file reader."""
    full = (ROOT_DIR / path).resolve()
    if not str(full).startswith(str(ROOT_DIR)): return "⛔ Access Denied"
    if full.suffix not in ALLOWED_EXTENSIONS: return f"⛔ File type {full.suffix} not allowed in Vault"
    try: return full.read_text(encoding="utf-8", errors="replace")
    except Exception as e: return str(e)