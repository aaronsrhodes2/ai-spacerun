"""Call the factorio MCP tools from a script, using the same RCON settings and tunnel."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import mcp_server  # noqa: E402

tools = {t.name: t.fn for t in mcp_server.mcp._tool_manager.list_tools()}
