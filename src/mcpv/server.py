import os
import asyncio
import logging
import json
from pathlib import Path
from fastmcp import FastMCP
from .valve import valve
from .vault import manager
from .platform_abstraction import platform_info

# 1. 설정 및 로깅 (Cross-platform)
CONFIG_DIR = platform_info.get_config_dir()
try: CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except: pass
LOG_FILE = CONFIG_DIR / "mcpv_debug.log"
ROOT_PATH_FILE = CONFIG_DIR / "root_path.txt"

logging.basicConfig(filename=str(LOG_FILE), level=logging.DEBUG, force=True, encoding="utf-8")
logger = logging.getLogger("mcpv-router")

# CWD 설정 (기존 유지)
if ROOT_PATH_FILE.exists():
    try:
        os.chdir(Path(ROOT_PATH_FILE.read_text(encoding="utf-8").strip()).resolve())
    except: pass
ROOT_DIR = Path.cwd().resolve()

mcp = FastMCP("mcpv")

# === Timeout Constants (REQ-01, REQ-02) ===
GATHER_TIMEOUT = 30.0  # Overall timeout for connecting to all servers
TOOL_LIST_TIMEOUT = 3.0  # Timeout per server for listing tools

# === 🌟 [핵심 1] 글로벌 툴 레지스트리 (지도) ===
# 구조: { "tool_name": { "server": "server_name", "desc": "description...", "args": "arg1, arg2" } }
TOOL_REGISTRY = {}
TOOL_INDEX_FILE = CONFIG_DIR / "tool_index.json"

async def _build_registry():
    """Builds tool map by scanning upstream servers. Uses local cache if available."""
    global TOOL_REGISTRY
    from .vault import BACKUP_FILE
    
    # 1. 시도: 로컬 캐시 먼저 읽기
    if not TOOL_REGISTRY and TOOL_INDEX_FILE.exists():
        try:
            with open(TOOL_INDEX_FILE, "r", encoding="utf-8") as f:
                TOOL_REGISTRY = json.load(f)
                logger.info("⚡ Tool Registry loaded from local cache.")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load tool cache: {e}")

    if not BACKUP_FILE.exists(): return
    
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    active_servers = [k for k, v in config.get("mcpServers", {}).items() if not v.get("disabled")]
    
    # 병렬 연결 시도 (REQ-01: timeout wrapper)
    tasks = [manager.get_session(name) for name in active_servers]
    try:
        sessions = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=GATHER_TIMEOUT
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout ({GATHER_TIMEOUT}s) connecting to servers")
        return  # Exit early, use cached registry if available
    
    new_registry = {}
    
    for name, session in zip(active_servers, sessions):
        if not session or isinstance(session, Exception):
            if isinstance(session, Exception):
                logger.warning(f"Failed to connect to {name}: {session}")
            continue
        try:
            tools = await asyncio.wait_for(session.list_tools(), timeout=TOOL_LIST_TIMEOUT)
            for t in tools.tools:
                key = t.name
                if key in new_registry:
                    key = f"{name}_{t.name}"
                
                args = list(t.inputSchema.get("properties", {}).keys())
                new_registry[key] = {
                    "server": name,
                    "real_name": t.name,
                    "desc": t.description[:150] if t.description else "No description",
                    "args": ", ".join(args)
                }
        except asyncio.TimeoutError:
            logger.warning(f"Timeout listing tools from {name}")
            continue
        except Exception as e:
            logger.warning(f"Error listing tools from {name}: {e}")
            continue
            
    if new_registry:
        TOOL_REGISTRY = new_registry
        # 로컬 파일에 캐시 저장
        try:
            with open(TOOL_INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(TOOL_REGISTRY, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to save tool cache: {e}")
        logger.info(f"🗺️ Tool Registry Rebuilt and Cached: {len(TOOL_REGISTRY)} tools found.")

# === 🌟 [핵심 2] 스마트 컨텍스트 주입 (압축 모드) ===
@mcp.tool()
async def get_initial_context(force: bool = False) -> str:
    """
    [System Start] Initializes the session.
    Returns a summary of available tools to save tokens and prevent truncation.
    """
    # 1. 밸브 체크
    allowed, msg = valve.check(force)
    if not allowed: return msg
    
    # 2. 레지스트리 빌드 (서버 깨우기)
    await _build_registry()
    
    if not TOOL_REGISTRY:
        return "⚠️ No tools found in connected MCP servers."

    # 3. 서버별 도구 목록 요약 (이름만)
    servers = {}
    for t_name, info in TOOL_REGISTRY.items():
        srv = info['server']
        if srv not in servers: servers[srv] = []
        servers[srv].append(t_name)
    
    manual = [
        "=== 🎮 MCPV SMART CONSOLE (Vault v0.4) ===",
        "Performance optimization: compact tool names are listed. Use 'mcpv_admin' for details.",
        f"Detected {len(servers)} active servers and {len(TOOL_REGISTRY)} total tools.\n",
        "--- Quick Search (Vaulted Tools) ---"
    ]
    
    for srv, tools in servers.items():
        # Add 'vault:' prefix to indicate these are NOT direct functions
        prefixed_tools = [f"vault:{t}" for t in tools[:20]]
        tool_fmt = ", ".join(prefixed_tools)
        if len(tools) > 20: tool_fmt += "..."
        manual.append(f"📦 {srv} ({len(tools)}): {tool_fmt}")
    
    manual.append("\n=== [🚀 CRITICAL: Access Modes] ===")
    manual.append("1. DIRECT TOOLS (e.g., mcp_exa_*): Call these directly as functions.")
    manual.append("2. VAULTED TOOLS (marked 'vault:...'): You MUST use the mcp_mcp-vault_run_tool proxy.")
    manual.append("   - Example: call run_tool(tool_name='brave_web_search', args={...})")
    manual.append("   - DO NOT call vaulted names directly.")
    manual.append("\n- VIEW FULL SCHEMA: call 'mcp_mcp-vault_mcpv_admin(action=\"list_tools\", params={\"server_name\": \"...\"})'")
    manual.append("- RUN A TOOL      : call 'run_tool(tool_name=\"...\", args={...})'")
    manual.append("\nTip: Just use the tool name in 'run_tool'. Arguments can be guessed or seen in full schema.")
    
    return "\n".join(manual)

# === 🌟 [Admin Console] (Unified Management) ===

@mcp.tool()
async def mcpv_admin(action: str, params: dict = {}) -> str:
    """
    Unified administration console for MCP Vault.
    Actions: 
    - list_servers: List all upstream servers and status.
    - list_tools: Show detailed tools for a server (params: {'server_name': '...'}).
    - search: Search tools by keyword (params: {'query': '...'}).
    - toggle_server: Enable/disable server (params: {'server_name': '...', 'enabled': bool}).
    - toggle_tool: Enable/disable tool (params: {'server_name': '...', 'tool_name': '...', 'enabled': bool}).
    """
    if action == "list_servers":
        from .vault import BACKUP_FILE
        if not BACKUP_FILE.exists(): return "❌ Vault backup not found."
        with open(BACKUP_FILE, "r", encoding="utf-8") as f: config = json.load(f)
        servers = config.get("mcpServers", {})
        output = ["=== 🛰️ UPSTREAM SERVERS ==="]
        for name, srv in servers.items():
            status = "🔴 DISABLED" if srv.get("disabled") else "🟢 ACTIVE"
            output.append(f"- {name:20} | {status}")
        return "\n".join(output)

    elif action == "list_tools":
        server_name = params.get("server_name")
        if not server_name: return "❌ Missing param 'server_name'."
        if not TOOL_REGISTRY: await _build_registry()
        relevant = {k: v for k, v in TOOL_REGISTRY.items() if v['server'] == server_name}
        if not relevant: return f"⚠️ No active tools for '{server_name}'."
        output = [f"=== 🛠️ TOOLS for '{server_name}' ==="]
        for name, info in relevant.items():
            output.append(f"🔹 {name}\n   └─ Args: {info['args']}\n   └─ Desc: {info['desc']}\n")
        return "\n".join(output)

    elif action == "search":
        query = params.get("query", "").lower()
        if not query: return "❌ Missing param 'query'."
        if not TOOL_REGISTRY: await _build_registry()
        matches = [f"🔍 {name} ({info['server']})\n   └─ Desc: {info['desc']}" 
                   for name, info in TOOL_REGISTRY.items() 
                   if query in name.lower() or query in info['desc'].lower()]
        return "=== 🔎 SEARCH RESULTS ===\n" + "\n\n".join(matches) if matches else "❌ No matches."

    elif action == "toggle_server":
        server_name, enabled = params.get("server_name"), params.get("enabled", True)
        if not server_name: return "❌ Missing param 'server_name'."
        success = manager.update_config(server_name, "disabled", not enabled)
        return f"✅ Server '{server_name}' is now {'ENABLED' if enabled else 'DISABLED'}." if success else "❌ Update failed."

    elif action == "toggle_tool":
        server_name, tool_name, enabled = params.get("server_name"), params.get("tool_name"), params.get("enabled", True)
        if not (server_name and tool_name): return "❌ Missing params."
        success = manager.update_disabled_tools(server_name, tool_name, not enabled)
        return f"✅ Tool '{tool_name}' on '{server_name}' is now {'ENABLED' if enabled else 'DISABLED'}." if success else "❌ Update failed."

    return "❌ Invalid action. Available: list_servers, list_tools, search, toggle_server, toggle_tool"

# === 🌟 [핵심 3] 통합 실행 도구 (Flattened Execution) ===
# === 🌟 [업그레이드] 스마트 실행 도구 (Auto-Correction 탑재) ===
@mcp.tool()
async def run_tool(tool_name: str, args: dict = {}) -> str:
    """
    Executes ANY tool from the available list.
    Smart Router: Automatically finds the correct server for the tool.
    """
    # 1. 레지스트리 로드 (없으면 빌드)
    if not TOOL_REGISTRY:
        await _build_registry()

    # 2. [FIX] Normalization & Prefix Removal
    # Handle 'vault:' prefix or 'mcp_' prefix hallucinations
    target_name = tool_name
    if target_name.startswith("vault:"):
        target_name = target_name[6:]
    elif target_name.startswith("mcp_"):
        # Attempt to find the tool name even if the model tries to call it like a direct tool
        for reg_name in TOOL_REGISTRY.keys():
            if target_name.endswith(reg_name):
                target_name = reg_name
                break
        
    # 3. 정확한 매칭 (Happy Path)
    info = TOOL_REGISTRY.get(target_name)
    
    # 4. [NEW] 매칭 실패 시: 에이전트 실수 교정 로직
    if not info:
        # A. 혹시 서버 이름을 도구 이름으로 착각했나? (예: context-7 -> context7)
        # 툴 레지스트리에서 서버 목록 추출
        known_servers = set(t['server'] for t in TOOL_REGISTRY.values())
        
        # 입력값과 서버명을 정규화(특수문자 제거, 소문자)해서 비교
        normalized_input = tool_name.replace("-", "").replace("_", "").lower()
        
        target_server = None
        for sv in known_servers:
            if normalized_input == sv.replace("-", "").replace("_", "").lower():
                target_server = sv
                break
        
        if target_server:
            # 해당 서버에 속한 진짜 도구들을 찾아서 제안
            server_tools = [
                f"'{name}' (Args: {i['args']})" 
                for name, i in TOOL_REGISTRY.items() 
                if i['server'] == target_server
            ]
            return (
                f"🛑 Error: '{tool_name}' appears to be a SERVER name (or typo), not a TOOL name.\n"
                f"The server '{target_server}' has the following tools:\n"
                f"{chr(10).join(['- ' + t for t in server_tools])}\n\n"
                f"👉 Please retry 'run_tool' with one of the tool names above."
            )

        # B. 단순히 도구 이름 오타인가? (유사도 검색)
        candidates = [k for k in TOOL_REGISTRY.keys() if tool_name in k or k in tool_name]
        if candidates:
            return f"❌ Tool '{tool_name}' not found. Did you mean one of these?\n- " + "\n- ".join(candidates)
            
        return f"❌ Tool '{tool_name}' not found in Registry. Please call 'get_initial_context' to see the full menu."

    # 4. 실행 로직 (기존과 동일)
    server_name = info['server']
    real_tool_name = info['real_name']
    
    try:
        session = await manager.get_session(server_name)
        # 세션 연결 실패 시 재시도 로직이나 안내 메시지 등은 manager 내부 혹은 여기서 처리
        if not session:
            return f"❌ Failed to connect to server '{server_name}'."

        result = await session.call_tool(real_tool_name, args)
        
        output = []
        if hasattr(result, 'content'):
            for c in result.content:
                if c.type == "text": output.append(c.text)
                else: output.append(f"[{c.type} content]")
        
        final_res = "\n".join(output) if output else "✅ Executed (No output)"
        return final_res
        
    except Exception as e:
        return f"❌ Execution Error ({server_name} -> {tool_name}): {e}"

# --- 기존 필수 유틸리티 (파일 읽기 등) ---
@mcp.tool()
def read_file(path: str) -> str:
    """Reads a file from the project root."""
    try:
        p = (ROOT_DIR / path).resolve()
        # Resolve symlinks and verify strict containment
        p = p.resolve(strict=True)
        try:
            # Use os.path.commonpath for robust containment check
            os.path.commonpath([ROOT_DIR, p])
        except ValueError:
            return "⛔ Access Denied"
        if not p.is_relative_to(ROOT_DIR):
            return "⛔ Access Denied"
        return p.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return "❌ File not found"
    except Exception as e:
        return f"❌ Error: {e}"

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """Lists files in a directory."""
    try:
        p = (ROOT_DIR / path).resolve()
        # Resolve symlinks and verify strict containment
        p = p.resolve(strict=True)
        try:
            os.path.commonpath([ROOT_DIR, p])
        except ValueError:
            return "⛔ Access Denied"
        if not p.is_relative_to(ROOT_DIR):
            return "⛔ Access Denied"
        out = []
        with os.scandir(p) as it:
            for e in it:
                if not e.name.startswith("."): out.append(e.name)
        return "\n".join(out)
    except FileNotFoundError:
        return "❌ Directory not found"
    except Exception as e:
        return f"❌ Error: {e}"

# JIT Initialized on first call.
# @mcp.on_startup()
async def on_startup():
    """Warms up the registry in the background when the server starts."""
    logger.info("🚀 [MCPV] Starting background registry warmup...")
    # 비동기로 빌드 진행 (이전 캐시 로드 포함)
    asyncio.create_task(_build_registry())