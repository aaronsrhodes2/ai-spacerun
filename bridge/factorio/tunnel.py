"""
Self-healing SSH tunnel to the RCON port of a Factorio server in Docker.

RCON is deliberately not published on the game VM, so we forward a local port
to the container's internal address. That address can change when the container
is recreated, and the VM sleeps when idle, so a thread re-checks every minute
and reopens the tunnel when needed.

Enabled by FACTORIO_SSH_TARGET in bridge/.env. Without it nothing starts and
RCON is used directly, which is what hosting a save on this PC needs.
"""

import atexit
import logging
import subprocess
import sys
import threading
import time

log = logging.getLogger(__name__)

_CHECK_SECONDS = 60
_SSH_OPTS = [
    "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "ConnectTimeout=10",
]
# Never inherit stdin/stdout: the MCP server speaks its protocol over them.
_QUIET = {
    "stdin": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL,
    "creationflags": subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
}


def _container_ip(target: str, container: str) -> str | None:
    fmt = "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"
    try:
        r = subprocess.run(
            ["ssh", *_SSH_OPTS, target, f"docker inspect -f '{fmt}' {container}"],
            stdout=subprocess.PIPE, text=True, timeout=30, **_QUIET,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        log.info("tunnel: cannot reach %s: %s", target, e)
        return None
    ip = r.stdout.strip()
    return ip if r.returncode == 0 and ip else None


def _run(target: str, container: str, local_port: int, remote_port: int) -> None:
    proc = None
    current_ip = None

    def stop() -> None:
        if proc and proc.poll() is None:
            proc.terminate()

    atexit.register(stop)

    while True:
        ip = _container_ip(target, container)
        if ip and (ip != current_ip or proc is None or proc.poll() is not None):
            stop()
            log.info("tunnel: 127.0.0.1:%d -> %s:%d via %s", local_port, ip, remote_port, target)
            # If something else already holds the local port this exits at once
            # and the next check tries again.
            proc = subprocess.Popen(
                ["ssh", "-N", *_SSH_OPTS,
                 "-o", "ExitOnForwardFailure=yes",
                 "-o", "ServerAliveInterval=30",
                 "-o", "ServerAliveCountMax=3",
                 "-L", f"127.0.0.1:{local_port}:{ip}:{remote_port}",
                 target],
                stdout=subprocess.DEVNULL, **_QUIET,
            )
            current_ip = ip
        time.sleep(_CHECK_SECONDS)


def start(target: str, container: str, local_port: int, remote_port: int = 27015) -> None:
    """Keep the tunnel up from a daemon thread. Returns immediately."""
    threading.Thread(
        target=_run, args=(target, container, local_port, remote_port),
        name="rcon-tunnel", daemon=True,
    ).start()
