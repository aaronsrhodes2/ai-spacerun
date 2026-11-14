#!/usr/bin/env bash
# The local test server for the Skippy mod: a second, headless copy of the Steam install with its own data folder
# (.testserver/, not in git). It never touches the live game or the player's own Factorio folder.
#   modserver.sh start   copy the mod in and run the server (foreground; run it in the background from the caller)
#   modserver.sh stop    stop the test server only (matched by its config path, never the player's client)
#   modserver.sh new     make a fresh test map
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd -W 2>/dev/null || pwd)"
F="/d/Steam/steamapps/common/Factorio/bin/x64/Factorio.exe"
T="$ROOT/.testserver"
sync_mod() { rm -rf "$T/data/mods/skippy-copilot"; cp -r "$ROOT/mods/skippy-copilot" "$T/data/mods/"; }
case "$1" in
  stop)  powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='factorio.exe'\" | Where-Object { \$_.CommandLine -match '\.testserver' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force; 'stopped ' + \$_.ProcessId }" ;;
  new)   sync_mod; rm -f "$T/data/saves/test.zip"; "$F" --config "$T/config.ini" --create "$T/data/saves/test.zip" 2>&1 | tail -2 ;;
  start) sync_mod; "$F" --config "$T/config.ini" --start-server "$T/data/saves/test.zip" --port 34198 --rcon-bind 127.0.0.1:27116 --rcon-password "$(cat "$T/rcon.pw")" 2>&1 | grep --line-buffered -v -i password ;;
  *) echo "usage: modserver.sh start|stop|new"; exit 1 ;;
esac
