import typer
import asyncio
from .vault import manager
from .server import mcp

app = typer.Typer()

@app.command()
def install(
    force: bool = typer.Option(False, "--force", "-f", help="Force install even if only 1 MCP exists.")
):
    """Installs mcpv as the primary gateway in Antigravity."""
    print("🛡️  Installing MCP Vault...")
    # force 옵션을 manager에게 전달
    manager.install(force=force)
    
    # 설치가 취소되었을 수도 있으므로 메시지는 vault.py에서 출력된 내용을 참고
    print("👉 Check the output above.")

@app.command()
def start():
    """Starts the mcpv server (Used by Antigravity)."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.run(manager.cleanup())

if __name__ == "__main__":
    app()