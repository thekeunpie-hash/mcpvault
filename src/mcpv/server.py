import os
import asyncio
import logging
import json
from pathlib import Path
from fastmcp import FastMCP
from .valve import valve
from .vault import manager

# 1. 설정 및 로깅 (기존 유지)
CONFIG_DIR = Path.home() / ".gemini" / "antigravity"
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

# === 🌟 [핵심 1] 글로벌 툴 레지스트리 (지도) ===
# 구조: { "tool_name": { "server": "server_name", "desc": "description...", "args": "arg1, arg2" } }
TOOL_REGISTRY = {}

async def _build_registry():
    """모든 업스트림 서버를 스캔하여 도구 지도를 만듭니다."""
    global TOOL_REGISTRY
    from .vault import BACKUP_FILE
    
    if not BACKUP_FILE.exists(): return
    
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    active_servers = [k for k, v in config.get("mcpServers", {}).items() if not v.get("disabled")]
    
    # 병렬 연결 시도
    tasks = [manager.get_session(name) for name in active_servers]
    sessions = await asyncio.gather(*tasks, return_exceptions=True)
    
    new_registry = {}
    
    for name, session in zip(active_servers, sessions):
        if not session or isinstance(session, Exception): continue
        try:
            # 타임아웃을 두고 도구 목록 획득
            tools = await asyncio.wait_for(session.list_tools(), timeout=3.0)
            for t in tools.tools:
                # 툴 이름 충돌 방지: 만약 이미 있으면 'server_toolname'으로 등록
                key = t.name
                if key in new_registry:
                    key = f"{name}_{t.name}" # 충돌 시 접두사 붙임
                
                args = list(t.inputSchema.get("properties", {}).keys())
                new_registry[key] = {
                    "server": name,
                    "real_name": t.name, # 실제 호출할 이름
                    "desc": t.description[:100] if t.description else "No description",
                    "args": ", ".join(args)
                }
        except:
            continue
            
    TOOL_REGISTRY = new_registry
    logger.info(f"🗺️ Tool Registry Built: {len(TOOL_REGISTRY)} tools found.")

# === 🌟 [핵심 2] 스마트 컨텍스트 주입 ===
@mcp.tool()
async def get_initial_context(force: bool = False) -> str:
    """
    [System Start] Initializes the session.
    Returns a 'Tool Manual' so you know what tools are available.
    Does NOT return full code context to save tokens (use 'read_file' if needed).
    """
    # 1. 밸브 체크
    allowed, msg = valve.check(force)
    if not allowed: return msg
    
    # 2. 레지스트리 빌드 (서버 깨우기)
    await _build_registry()
    
    if not TOOL_REGISTRY:
        return "⚠️ No tools found in connected MCP servers."

    # 3. 메뉴판(Manual) 생성
    manual = [
        "=== 🎮 MCPV SMART CONSOLE ===",
        "You have access to the following tools. DO NOT use 'use_upstream_tool'.",
        "JUST use 'run_tool(name=...)' directly.\n",
        "--- Available Tools ---"
    ]
    
    # 툴 목록을 예쁘게 정리
    for tool_name, info in TOOL_REGISTRY.items():
        manual.append(f"🔹 {tool_name}")
        manual.append(f"   └─ Args: {info['args']}")
        manual.append(f"   └─ Desc: {info['desc']}")
    
    manual.append("\n=== [Instruction] ===")
    manual.append("To execute any tool above, use:")
    manual.append("run_tool(tool_name='TOOL_NAME', args={...})")
    manual.append("Example: run_tool(tool_name='query-docs', args={'query': 'nextjs'})")
    
    return "\n".join(manual)

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
        
    # 2. 정확한 매칭 (Happy Path)
    info = TOOL_REGISTRY.get(tool_name)
    
    # 3. [NEW] 매칭 실패 시: 에이전트 실수 교정 로직
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
        if not str(p).startswith(str(ROOT_DIR)): return "⛔ Access Denied"
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e: return str(e)

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """Lists files in a directory."""
    try:
        p = (ROOT_DIR / path).resolve()
        out = []
        with os.scandir(p) as it:
            for e in it:
                if not e.name.startswith("."): out.append(e.name)
        return "\n".join(out)
    except Exception as e: return str(e)