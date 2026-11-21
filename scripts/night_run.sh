#!/usr/bin/env bash
# The night run: the bridge's configured source (purple Skippy, from copilot/copilot.env) playing on the test server
# (on skippy-core, see modserver.sh; a fresh map from the fixed seed each run), with a Factorio client on this card
# (video memory usage low, windowed) so the client's share of video memory is measured. No model is loaded locally: the
# Captain's word (2026-11-20) is to use purple; the Qwen3 8B floor is a design target the context tests hold, not a live
# run. Test server and test client only: never the live game, never the player's own client. While the player's own
# Factorio is open it runs without the test client (the server is on skippy-core), or not at all with MODSERVER_HOST=local.
#   bash scripts/night_run.sh          results in runs/night-<stamp>/ (summary.txt first)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="runs/night-$STAMP"
mkdir -p "$OUT"
SUM="$OUT/summary.txt"
note() { echo "$(date +%H:%M:%S) $*" | tee -a "$SUM"; }
vram() { nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -1; }
phase() { note "phase $1: video memory used/total MiB = $(vram)"; }
cleanup() {
  note "cleaning up"
  kill "$SAMPLER" 2>/dev/null
  bash scripts/modserver.sh stop >> "$OUT/server.log" 2>&1
  note "done; test server and test client stopped"
}

# ---- the player's own game must not be running
OWN=$(powershell.exe -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='factorio.exe'\" | Where-Object { \$_.CommandLine -notmatch '\.test(server|client)' }).Count" | tr -d '\r')
CLIENT=yes
if [ "${OWN:-0}" != "0" ]; then
  if [ "${MODSERVER_HOST:-skippy-core}" = "local" ]; then
    note "the player's own Factorio is open: not starting (no local test server while the Captain plays)"
    exit 3
  fi
  CLIENT=no                                # the server is on skippy-core (the Captain, 2026-11-21); only the client would load this card
  note "the player's own Factorio is open: running on skippy-core without the test client"
fi
core_mem() { ssh -o BatchMode=yes skippy-core "free -m | awk 'NR==2{print \$7}'" 2>/dev/null; }
if [ "$(curl -s -m 5 -o /dev/null -w "%{http_code}" http://127.0.0.1:47860/mcp)" = "000" ]; then
  note "purple's door (127.0.0.1:47860) is not answering: not starting"
  exit 4
fi
nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader -l 5 > "$OUT/vram.csv" 2>/dev/null &
SAMPLER=$!
trap cleanup EXIT
note "night run $STAMP: source from copilot.env (purple), server on ${MODSERVER_HOST:-skippy-core}, test client: $CLIENT"
phase "baseline (nothing of ours running)"
[ "${MODSERVER_HOST:-skippy-core}" != "local" ] && note "skippy-core memory available before: $(core_mem) MiB"

# ---- test server, on a fresh map from the fixed seed, waited for over RCON
bash scripts/modserver.sh new > "$OUT/new.log" 2>&1 || { note "making the test map failed (see new.log)"; exit 5; }
bash scripts/modserver.sh start > "$OUT/server.log" 2>&1 &
for i in $(seq 1 60); do
  python -c "import sys; sys.path.insert(0,'scripts'); from modtest import client; client().send_command('/skippy tools')" > /dev/null 2>&1 && break
  sleep 3
done
python -c "import sys; sys.path.insert(0,'scripts'); from modtest import client; client().send_command('/skippy tools')" > /dev/null 2>&1 \
  || { note "the test server did not answer over RCON in 3 minutes (see server.log)"; exit 5; }
note "test server up"
phase "test server only"
[ "${MODSERVER_HOST:-skippy-core}" != "local" ] && note "skippy-core memory available with the server up: $(core_mem) MiB"

# ---- test client, joined (not while the player's own game is open)
if [ "$CLIENT" = "yes" ]; then
  bash scripts/modserver.sh client > "$OUT/client.log" 2>&1 &
  JOINED=no
  for i in $(seq 1 120); do                # up to six minutes: Steam restarts the client and its sprites load first
    N=$(python scripts/modtest.py --lua "rcon.print(#game.connected_players)" 2>/dev/null | tr -d '\r' | tail -1)
    [ "$N" = "1" ] && { JOINED=yes; break; }
    sleep 3
  done
  note "test client joined: $JOINED"
  sleep 30
  phase "test server and client"
fi

# ---- the checks and the leg, against the test server only
# COPILOT_GAME=test (copilot/games.py): the test server's address whatever copilot.env says, its map seed checked, its
# own plans, and purple's turns name its own door (skippy-copilot-test in .mcp.json), never the live game's
export COPILOT_GAME=test
export COPILOT_RCON_HOST=127.0.0.1 COPILOT_RCON_PORT=27116 COPILOT_RCON_PASSWORD_FILE=.testserver/rcon.pw
export COPILOT_QUICK_URL= COPILOT_PURPLE_URL=off COPILOT_VOICE_PORT=off COPILOT_LOG_DIR="$OUT"   # purple alone; no voice door
python scripts/modcheck.py > "$OUT/modcheck.txt" 2>&1; note "modcheck: exit $? ($(grep -c '^FAIL' "$OUT/modcheck.txt") failed)"
python scripts/nightcheck.py > "$OUT/nightcheck.txt" 2>&1; note "nightcheck: exit $? ($(grep -c '^FAIL' "$OUT/nightcheck.txt") failed)"
python -m copilot --check > "$OUT/setup-check.txt" 2>&1; note "setup check: exit $?"
if ! grep -q '"skippy-copilot-test"' .mcp.json; then          # without its own door purple could only reach the live game
  note "first leg skipped: .mcp.json has no skippy-copilot-test server, so purple has no door to the test game"
else
timeout 10800 python -m copilot.leg copilot/legs/first.txt > "$OUT/leg.txt" 2>&1; note "first leg: exit $? ($(tail -n 30 "$OUT/leg.txt" | grep -m1 -i 'leg-' || echo 'no score line'))"
fi
[ -f "$OUT/report.html" ] && note "the run page, a picture per turn: $OUT/report.html ($(ls "$OUT"/turn-*.png 2>/dev/null | wc -l) pictures)"
phase "after the leg"
[ "${MODSERVER_HOST:-skippy-core}" != "local" ] && note "skippy-core memory available after the leg: $(core_mem) MiB"
PEAK=$(cut -d, -f2 "$OUT/vram.csv" | tr -dc '0-9\n' | sort -n | tail -1)
note "peak video memory used during the run: ${PEAK:-?} MiB (everything on the card, Windows and other programs included)"
