#!/usr/bin/env bash
# The local test server for the Skippy mod: a second, headless copy of the Steam install with its own data folder
# (.testserver/, not in git). It never touches the live game or the player's own Factorio folder.
#   modserver.sh start    copy the mod in and run the server (foreground; run it in the background from the caller)
#   modserver.sh client   a test client with its own folder (.testclient/, not in git) and exactly the server's mods,
#                         joined to the test server (foreground; run it in the background). The player's own client,
#                         its mods and its login are never used.
#   modserver.sh stop     stop the test server and the test client only (matched by their folders, never the player's client)
#   modserver.sh new      make a fresh test map
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd -W 2>/dev/null || pwd)"
F="/d/Steam/steamapps/common/Factorio/bin/x64/Factorio.exe"
T="$ROOT/.testserver"
C="$ROOT/.testclient"
sync_mod() { rm -rf "$1/data/mods/skippy-copilot"; cp -r "$ROOT/mods/skippy-copilot" "$1/data/mods/"; }
server_settings() {                         # a private test server: no account check, so the test client needs no login
  [ -f "$T/server-settings.json" ] || printf '%s\n' '{' '  "name": "skippy-test", "description": "local test server",' \
    '  "visibility": { "public": false, "lan": false },' '  "require_user_verification": false,' \
    '  "max_players": 2, "auto_pause": false, "only_admins_can_pause_the_game": true,' '  "autosave_interval": 0' '}' > "$T/server-settings.json"
}
client_folder() {                           # the test client's own folder: the server's mod list, a name, no login token
  mkdir -p "$C/data/mods"
  [ -f "$C/config.ini" ] || printf '%s\n' '[path]' 'read-data=__PATH__executable__/../../data' "write-data=$ROOT/.testclient/data" \
    '[other]' 'check-updates=false' > "$C/config.ini"
  cp "$T/data/mods/mod-list.json" "$C/data/mods/mod-list.json"
  [ -f "$C/data/player-data.json" ] || printf '%s\n' '{ "service-username": "skippy-test" }' > "$C/data/player-data.json"
}
case "$1" in
  stop)   powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='factorio.exe'\" | Where-Object { \$_.CommandLine -match '\.test(server|client)' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force; 'stopped ' + \$_.ProcessId }" ;;
  new)    sync_mod "$T"; rm -f "$T/data/saves/test.zip"; "$F" --config "$T/config.ini" --create "$T/data/saves/test.zip" 2>&1 | tail -2 ;;
  start)  sync_mod "$T"; server_settings
          "$F" --config "$T/config.ini" --start-server "$T/data/saves/test.zip" --server-settings "$T/server-settings.json" --port 34198 \
            --rcon-bind 127.0.0.1:27116 --rcon-password "$(cat "$T/rcon.pw")" 2>&1 | grep --line-buffered -v -i password ;;
  client) client_folder; sync_mod "$C"; "$F" --config "$C/config.ini" --mp-connect 127.0.0.1:34198 2>&1 | tail -20 ;;
  *) echo "usage: modserver.sh start|client|stop|new"; exit 1 ;;
esac
