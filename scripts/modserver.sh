#!/usr/bin/env bash
# The test server for the Skippy mod. It never touches the live game or the player's own Factorio folder.
# Where it runs (MODSERVER_HOST):
#   skippy-core (the default)  a headless Linux copy in ~/factorio-test on skippy-core, so tests can run while the Captain
#                              plays on this PC (the Captain, 2026-11-21). RCON stays on skippy-core's loopback and comes
#                              here through the ssh session that runs the server, so 127.0.0.1:27116 works as before.
#   local                      a second, headless copy of the Steam install with its own data folder (.testserver/, not in git)
#   modserver.sh start    copy the mod in and run the server (foreground; run it in the background from the caller)
#   modserver.sh client   a test client with its own folder (.testclient/, not in git) and exactly the server's mods,
#                         joined to the test server (foreground; run it in the background). The player's own client,
#                         its mods and its login are never used.
#   modserver.sh stop     stop the test server and the test client only (matched by their folders, never the player's client)
#   modserver.sh new      make a fresh test map, always from the same seed so every run sees the same ground
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd -W 2>/dev/null || pwd)"
RU="$(cd "$(dirname "$0")/.." && pwd)"           # the same folder as this shell writes it, for tar
HOST="${MODSERVER_HOST:-skippy-core}"
SEED=20261121                                    # the test map's seed: change it only with the checks that read its ground
F="/d/Steam/steamapps/common/Factorio/bin/x64/Factorio.exe"
T="$ROOT/.testserver"
C="$ROOT/.testclient"
R='$HOME/factorio-test'                          # on skippy-core, expanded there
RF="$R/factorio/bin/x64/factorio"
sync_mod() { rm -rf "$1/data/mods/skippy-copilot"; cp -r "$ROOT/mods/skippy-copilot" "$1/data/mods/"; }
server_settings() {                         # a private test server: no account check, so the test client needs no login
  [ -f "$T/server-settings.json" ] || printf '%s\n' '{' '  "name": "skippy-test", "description": "local test server",' \
    '  "visibility": { "public": false, "lan": false },' '  "require_user_verification": false,' \
    '  "max_players": 2, "auto_pause": false, "only_admins_can_pause_the_game": true,' '  "autosave_interval": 0' '}' > "$T/server-settings.json"
}
remote_sync() {                             # the mod, its mod list and settings, the server settings and the RCON password, to skippy-core
  server_settings
  ssh -o BatchMode=yes "$HOST" "mkdir -p $R/data/mods $R/data/saves && rm -rf $R/data/mods/skippy-copilot $R/data/mods/skippy-quality && \
    printf '%s\n' '[path]' 'read-data=__PATH__executable__/../../data' \"write-data=$R/data\" '[other]' 'check-updates=false' > $R/config.ini"
  tar -C "$RU/mods" -cf - skippy-copilot skippy-quality | ssh -o BatchMode=yes "$HOST" "tar -C $R/data/mods -xf -"   # the mod list says which run
  tar -C "$RU/.testserver" -cf - server-settings.json rcon.pw data/mods/mod-list.json data/mods/mod-settings.dat \
    | ssh -o BatchMode=yes "$HOST" "tar -C $R -xf - && chmod 600 $R/rcon.pw"
}
client_folder() {                           # the test client's own folder: the server's mod list, a name, no login token
  mkdir -p "$C/data/mods"
  [ -f "$C/config.ini" ] || printf '%s\n' '[path]' 'read-data=__PATH__executable__/../../data' "write-data=$ROOT/.testclient/data" \
    '[other]' 'check-updates=false' '[graphics]' 'video-memory-usage=low' 'full-screen=false' > "$C/config.ini"   # as a player on a smaller card would set it
  grep -q '^full-screen=' "$C/config.ini" || sed -i 's/^\[graphics\]$/[graphics]\nfull-screen=false/' "$C/config.ini"   # the Captain: windowed, not full screen
  cp "$T/data/mods/mod-list.json" "$C/data/mods/mod-list.json"
  [ -f "$C/data/player-data.json" ] || printf '%s\n' '{ "service-username": "skippy-test" }' > "$C/data/player-data.json"
}
stop_local() {                              # the test client, a local test server, and the ssh session carrying RCON from skippy-core
  powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { (\$_.Name -eq 'factorio.exe' -and \$_.CommandLine -match '\.test(server|client)') -or (\$_.Name -eq 'ssh.exe' -and \$_.CommandLine -match '27116:127\.0\.0\.1:27116') } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force; 'stopped ' + \$_.Name + ' ' + \$_.ProcessId }"
}
if [ "$HOST" = "local" ]; then
  case "$1" in
    stop)   stop_local ;;
    new)    sync_mod "$T"; rm -f "$T/data/saves/test.zip"; "$F" --config "$T/config.ini" --create "$T/data/saves/test.zip" --map-gen-seed $SEED 2>&1 | tail -2 ;;
    start)  sync_mod "$T"; server_settings
            "$F" --config "$T/config.ini" --start-server "$T/data/saves/test.zip" --server-settings "$T/server-settings.json" --port 34198 \
              --rcon-bind 127.0.0.1:27116 --rcon-password "$(cat "$T/rcon.pw")" 2>&1 | grep --line-buffered -v -i password ;;
    client) client_folder; sync_mod "$C"; "$F" --config "$C/config.ini" --mp-connect 127.0.0.1:34198 2>&1 | tail -20 ;;
    *) echo "usage: modserver.sh start|client|stop|new"; exit 1 ;;
  esac
  exit
fi
case "$1" in
  stop)   ssh -o BatchMode=yes "$HOST" "pkill -f 'factorio-tes[t]/factorio/bin/x64/factorio' && echo 'stopped the test server on $HOST' || echo 'no test server running on $HOST'"
          stop_local ;;
  new)    remote_sync
          ssh -o BatchMode=yes "$HOST" "rm -f $R/data/saves/test.zip && $RF --config $R/config.ini --create $R/data/saves/test.zip --map-gen-seed $SEED 2>&1 | tail -2" ;;
  start)  remote_sync
          # the game port listens on skippy-core's tailnet address only; RCON on its loopback, forwarded here by this session
          ssh -o BatchMode=yes -o ExitOnForwardFailure=yes -L 27116:127.0.0.1:27116 "$HOST" \
            "exec $RF --config $R/config.ini --start-server $R/data/saves/test.zip --server-settings $R/server-settings.json --port 34198 \
              --bind \$(tailscale ip -4 | head -1) --rcon-bind 127.0.0.1:27116 --rcon-password \"\$(cat $R/rcon.pw)\"" 2>&1 | grep --line-buffered -v -i password ;;
  client) client_folder; sync_mod "$C"; "$F" --config "$C/config.ini" --mp-connect "$HOST:34198" 2>&1 | tail -20 ;;
  *) echo "usage: modserver.sh start|client|stop|new"; exit 1 ;;
esac
