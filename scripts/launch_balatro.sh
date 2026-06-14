#!/usr/bin/env bash
# Launch a Balatro instance directly via Proton (no Steam client), so the process
# is cleanly killable per-PID and multiple instances can run in parallel for
# training. Each instance gets its own wineprefix and TCP port (12345 + id),
# which the mod reads via BALATRO_ML_PORT (see mod/bridge.lua).
#
# Prerequisite (one-time, needs sudo — not installable unattended):
#     sudo apt install umu-launcher        # or your distro's package
# umu-launcher (https://github.com/Open-Wine-Components/umu-launcher) runs Proton
# games outside Steam and is the reliable path to clean kill + parallel instances.
#
# Usage:   scripts/launch_balatro.sh [instance_id]   (default 0)
# Prints the launched PID on stdout for clean teardown (kill -9 <pid>).

set -euo pipefail

INSTANCE_ID="${1:-0}"
BASE_PORT="${BML_BASE_PORT:-12345}"
PORT=$(( BASE_PORT + INSTANCE_ID ))

STEAM_ROOT="${STEAM_ROOT:-/home/court/snap/steam/common/.local/share/Steam}"
BALATRO_EXE="${BALATRO_EXE:-$STEAM_ROOT/steamapps/common/Balatro/Balatro.exe}"
PROTONPATH="${PROTONPATH:-$STEAM_ROOT/steamapps/common/Proton - Experimental}"
PREFIX_ROOT="${BML_PREFIX_ROOT:-$HOME/.local/share/BalatroML}"

if ! command -v umu-run >/dev/null 2>&1; then
  echo "ERROR: umu-run not found. Install it first:  sudo apt install umu-launcher" >&2
  echo "       (until then, use scripts/restart_balatro.sh for snap-Steam single-instance dev)" >&2
  exit 127
fi
if [ ! -f "$BALATRO_EXE" ]; then
  echo "ERROR: Balatro.exe not found at: $BALATRO_EXE" >&2
  exit 1
fi

export WINEPREFIX="$PREFIX_ROOT/instance_${INSTANCE_ID}"
export BALATRO_ML_PORT="$PORT"
export GAMEID="${GAMEID:-umu-default}"
export PROTONPATH
mkdir -p "$WINEPREFIX"

echo "Launching Balatro instance $INSTANCE_ID  (port $PORT, prefix $WINEPREFIX)" >&2
# Detached so it survives this shell; lovely injects via version.dll next to the
# exe regardless of launcher, so Steamodded + BalatroML still load.
setsid umu-run "$BALATRO_EXE" >/dev/null 2>&1 < /dev/null &
PID=$!
echo "$PID"
