#!/usr/bin/env bash
# The Skippy bridge on the live game (the Captain, 2026-11-21: "Write the script and start it"): what reads the Skippy
# panel in his game and answers in it, through purple Skippy (the source in copilot/copilot.env).
# It starts by itself (the Captain: "this should be part of the mod, don't make this a manual step"): a mod cannot start
# programs or open connections, so a Windows task runs this at every sign-in, and it connects whenever the game is up.
#   bash scripts/live_bridge.sh install    register the sign-in task SkippyFactorioBridge and start it now (once)
#   bash scripts/live_bridge.sh uninstall  stop it and remove the task
#   bash scripts/live_bridge.sh start      start it by hand (when not installed)
#   bash scripts/live_bridge.sh stop       stop it (it comes back at the next sign-in when installed)
#   bash scripts/live_bridge.sh status     is it running, and what it last said
# RCON is not published on the game VM, so an ssh tunnel brings the container's RCON to 127.0.0.1:27115, the address
# copilot/copilot.env and the gameplay chat's game tools use: whichever tunnel holds the port serves both. The address
# and password come from bridge/.env and are never printed. Logs go to runs/live/.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT=27115
TASK=SkippyFactorioBridge
OUT=runs/live
mkdir -p "$OUT"
val() { grep -m1 "^$1=" bridge/.env | cut -d= -f2- | tr -d '\r' | sed 's/^"//; s/"$//'; }
TARGET="$(val FACTORIO_SSH_TARGET)"
CONTAINER="$(val FACTORIO_SSH_CONTAINER)"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)

ours() {       # our tunnel and our bridge, by what only they carry on their command lines
  powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { (\$_.Name -eq 'ssh.exe' -and \$_.CommandLine -match 'ServerAliveCountMax=4') -or (\$_.Name -eq 'python.exe' -and \$_.CommandLine -match 'live_bridge=1') -or (\$_.Name -eq 'bash.exe' -and \$_.CommandLine -match 'live_bridge\.sh.? run') } | ForEach-Object { \$_.ProcessId }" | tr -d '\r'
}

tunnel() {
  local ip
  ip=$(ssh "${SSH_OPTS[@]}" "$TARGET" "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $CONTAINER" 2>/dev/null | tr -d '\r')
  [ -n "$ip" ] || { echo "$(date +%H:%M:%S) the game VM or its container did not answer; trying again" >> "$OUT/bridge.log"; return 1; }
  # ServerAliveCountMax=4 marks our tunnel: the gameplay chat's own (bridge/factorio/tunnel.py) says 3, and stop leaves it
  ssh -N "${SSH_OPTS[@]}" -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=4 \
    -L "127.0.0.1:$PORT:$ip:27015" "$TARGET" >> "$OUT/tunnel.log" 2>&1 &
  echo $! > "$OUT/tunnel.pid"
  sleep 3
}

case "${1:-start}" in
  start)
    if [ -n "$(ours)" ]; then echo "already running (bash scripts/live_bridge.sh stop first)"; exit 0; fi
    [ -n "$TARGET" ] && [ -n "$CONTAINER" ] || { echo "bridge/.env has no FACTORIO_SSH_TARGET or FACTORIO_SSH_CONTAINER"; exit 2; }
    nohup bash "$0" run > /dev/null 2>&1 &
    echo "started; logs in $OUT (bridge.log, tunnel.log); stop with: bash scripts/live_bridge.sh stop"
    ;;
  run)         # the keeper: the tunnel and the bridge, each brought back if it drops
    export COPILOT_GAME=live COPILOT_RCON_HOST=127.0.0.1 COPILOT_RCON_PORT=$PORT COPILOT_LOG_DIR="$OUT"   # copilot/games.py
    # purple's game turns run in their own workspace: the game skill and the doors, nothing else (copilot/play_workspace.py)
    COPILOT_WORKSPACE="$(python -m copilot.play_workspace 2>> "$OUT/bridge.log")" || COPILOT_WORKSPACE=f-ai-factorio
    export COPILOT_WORKSPACE
    COPILOT_RCON_PASSWORD="$(val FACTORIO_RCON_PASSWORD)"
    export COPILOT_RCON_PASSWORD
    unset COPILOT_RCON_PASSWORD_FILE
    while true; do
      if ! { [ -f "$OUT/tunnel.pid" ] && kill -0 "$(cat "$OUT/tunnel.pid")" 2>/dev/null; }; then tunnel || { sleep 30; continue; }; fi
      echo "$(date +%H:%M:%S) bridge starting" >> "$OUT/bridge.log"
      python -X live_bridge=1 -u -m copilot >> "$OUT/bridge.log" 2>&1
      echo "$(date +%H:%M:%S) bridge stopped (exit $?); again in 10 s" >> "$OUT/bridge.log"
      sleep 10
    done
    ;;
  install)
    win() { cygpath -w "$1"; }
    user="$USERNAME"
    [ -n "${USERDOMAIN:-}" ] && user="$USERDOMAIN\\$USERNAME"
    bash_exe="$(cygpath -w /)bin\\bash.exe"            # Git for Windows' launcher, which sets up PATH
    xml="$OUT/$TASK.task.xml"
    python - "$(win "$xml")" "$user" "$bash_exe" "$(cygpath -m "$ROOT/scripts/live_bridge.sh")" "$(win "$ROOT")" <<'PY'
import sys
out, user, bash, script, root = sys.argv[1:]
text = open("scripts/live_bridge.task.xml", encoding="utf-8").read()
for k, v in (("@USER@", user), ("@BASH@", bash), ("@SCRIPT@", script), ("@ROOT@", root)):
    text = text.replace(k, v.replace("&", "&amp;").replace("<", "&lt;"))
open(out, "w", encoding="utf-16").write(text)
PY
    MSYS_NO_PATHCONV=1 schtasks.exe /Create /TN "$TASK" /XML "$(win "$xml")" /F || exit 1
    bash "$0" stop > /dev/null
    MSYS_NO_PATHCONV=1 schtasks.exe /Run /TN "$TASK"
    echo "installed: it starts at every sign-in and is starting now"
    ;;
  uninstall)
    MSYS_NO_PATHCONV=1 schtasks.exe /End /TN "$TASK" > /dev/null 2>&1
    MSYS_NO_PATHCONV=1 schtasks.exe /Delete /TN "$TASK" /F
    bash "$0" stop
    ;;
  stop)
    MSYS_NO_PATHCONV=1 schtasks.exe /End /TN "$TASK" > /dev/null 2>&1      # first, or Windows restarts what is stopped
    pids=$(ours)
    if [ -z "$pids" ]; then echo "not running"; exit 0; fi
    for p in $pids; do powershell.exe -NoProfile -Command "Stop-Process -Id $p -Force" 2>/dev/null; done
    rm -f "$OUT/tunnel.pid"
    echo "stopped"
    ;;
  status)
    [ -n "$(ours)" ] && echo "running: $(ours | wc -l) processes" || echo "not running"
    tail -n 5 "$OUT/bridge.log" 2>/dev/null
    ;;
  *) echo "usage: live_bridge.sh [install|uninstall|start|stop|status]"; exit 1 ;;
esac
