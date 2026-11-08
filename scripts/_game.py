"""Call the factorio MCP tools from a script, using the same RCON settings and tunnel.

The SSH tunnel to a remote server is started here (and heals itself), so scripts no longer
depend on a hand-opened `ssh -L` that dies with the VM's idle shutdown."""
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import mcp_server  # noqa: E402

mcp_server._start_tunnel_if_configured()


def _wait_for_port(seconds=45):
    host, port = mcp_server._cfg.rcon.host, mcp_server._cfg.rcon.port
    end = time.time() + seconds
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1.5)
    return False


if not _wait_for_port():
    print("WARNING: RCON port isn't reachable (is the game VM awake?)", file=sys.stderr)

tools = {t.name: t.fn for t in mcp_server.mcp._tool_manager.list_tools()}
