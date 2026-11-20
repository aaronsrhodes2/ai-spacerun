#!/usr/bin/env bash
# The night run: the low bar (Qwen3 8B under Ollama) playing through the bridge on the local test server, with a Factorio
# client on the same card, so the 12 GB question is measured rather than guessed. Test server and test client only:
# never the live game, never the player's own client. Refuses to start while the player's own Factorio is open.
#   bash scripts/night_run.sh          results in runs/night-<stamp>/ (summary.txt first)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="runs/night-$STAMP"
mkdir -p "$OUT"
SUM="$OUT/summary.txt"
MODEL="qwen3:8b"
note() { echo "$(date +%H:%M:%S) $*" | tee -a "$SUM"; }
vram() { nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -1; }
phase() { note "phase $1: video memory used/total MiB = $(vram)"; }
cleanup() {
  note "cleaning up"
  kill "$SAMPLER" 2>/dev/null
  curl -s -m 20 http://127.0.0.1:11434/api/generate -d "{\"model\":\"$MODEL\",\"keep_alive\":0}" > /dev/null 2>&1   # unload the model
  bash scripts/modserver.sh stop >> "$OUT/server.log" 2>&1
  note "done; test server and test client stopped, model unloaded"
}

# ---- the player's own game must not be running
OWN=$(powershell.exe -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='factorio.exe'\" | Where-Object { \$_.CommandLine -notmatch '\.test(server|client)' }).Count" | tr -d '\r')
if [ "${OWN:-0}" != "0" ]; then
  note "the player's own Factorio is open: not starting (no live runs while the Captain plays)"
  exit 3
fi
if ! curl -s -m 5 http://127.0.0.1:11434/api/version > /dev/null; then
  note "Ollama is not answering on 127.0.0.1:11434: not starting"
  exit 4
fi
nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader -l 5 > "$OUT/vram.csv" 2>/dev/null &
SAMPLER=$!
trap cleanup EXIT
note "night run $STAMP: model $MODEL, tool groups on"
phase "baseline (nothing of ours running)"

# ---- test server, waited for over RCON
bash scripts/modserver.sh start > "$OUT/server.log" 2>&1 &
for i in $(seq 1 60); do
  python -c "import sys; sys.path.insert(0,'scripts'); from modtest import client; client().send_command('/skippy tools')" > /dev/null 2>&1 && break
  sleep 3
done
python -c "import sys; sys.path.insert(0,'scripts'); from modtest import client; client().send_command('/skippy tools')" > /dev/null 2>&1 \
  || { note "the test server did not answer over RCON in 3 minutes (see server.log)"; exit 5; }
note "test server up"
phase "test server only"

# ---- test client, joined
bash scripts/modserver.sh client > "$OUT/client.log" 2>&1 &
JOINED=no
for i in $(seq 1 60); do
  N=$(python scripts/modtest.py --lua "rcon.print(#game.connected_players)" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$N" = "1" ] && { JOINED=yes; break; }
  sleep 3
done
note "test client joined: $JOINED"
sleep 30
phase "test server and client"

# ---- the model loaded with the bridge's context size
curl -s -m 300 http://127.0.0.1:11434/api/generate -d "{\"model\":\"$MODEL\",\"prompt\":\"hello\",\"stream\":false,\"keep_alive\":\"60m\",\"options\":{\"num_ctx\":16384}}" > /dev/null
phase "client and model loaded (16k context)"
ollama ps 2>&1 | tee -a "$SUM"

# ---- the checks and the leg, against the test server only
export COPILOT_RCON_HOST=127.0.0.1 COPILOT_RCON_PORT=27116 COPILOT_RCON_PASSWORD_FILE=.testserver/rcon.pw
export COPILOT_SOURCE=ollama COPILOT_URL=http://127.0.0.1:11434 COPILOT_MODEL="$MODEL" COPILOT_NUM_CTX=16384
export COPILOT_PROVIDER=ollama COPILOT_BASE_URL=http://127.0.0.1:11434          # the names copilot.leg reads
export COPILOT_QUICK_URL= COPILOT_PURPLE_URL=off COPILOT_VOICE_PORT=off COPILOT_TOOL_GROUPS=on COPILOT_LOG_DIR="$OUT"
python scripts/modcheck.py > "$OUT/modcheck.txt" 2>&1; note "modcheck: exit $? ($(grep -c '^FAIL' "$OUT/modcheck.txt") failed)"
python scripts/nightcheck.py > "$OUT/nightcheck.txt" 2>&1; note "nightcheck: exit $? ($(grep -c '^FAIL' "$OUT/nightcheck.txt") failed)"
python -m copilot --check > "$OUT/setup-check.txt" 2>&1; note "setup check: exit $?"
timeout 5400 python -m copilot.leg copilot/legs/first.txt > "$OUT/leg.txt" 2>&1; note "first leg: exit $? ($(tail -n 30 "$OUT/leg.txt" | grep -m1 -i 'leg-' || echo 'no score line'))"
phase "after the leg"
PEAK=$(cut -d, -f2 "$OUT/vram.csv" | tr -dc '0-9\n' | sort -n | tail -1)
note "peak video memory used during the run: ${PEAK:-?} MiB (the 12 GB bar is 12288 MiB, including Windows and anything else open)"
