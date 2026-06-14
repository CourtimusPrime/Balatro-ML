#!/usr/bin/env bash
# Restart Balatro and wait until it's back at the menu (mod connectable).
#
# Two backends:
#   * umu-run present  -> clean per-PID kill + direct Proton relaunch (preferred;
#                         needed for parallel instances). Pass an instance id.
#   * else (snap-Steam) -> single-instance fallback. Per-PID kill is resisted by
#                         the snap PID namespace, so we process-GROUP kill (which
#                         also stops the Steam client), then relaunch Steam and the
#                         game. (See memory: balatro-live-test-setup.)
#
# NOTE: With mod hot-reload (scripts/reload_mod.py) you should rarely need this —
# launch once, then reload logic.lua in ~seconds without a restart. Use this only
# to (re)load bridge.lua/state.lua changes or recover a wedged game.
#
# Usage:   scripts/restart_balatro.sh [instance_id]   (default 0)

set -uo pipefail
INSTANCE_ID="${1:-0}"
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

real_game_up() { ps -eo args | grep -v grep | grep -q 'S:\\common\\Balatro\\Balatro.exe'; }

wait_for_menu() {  # poll for the real game exe, then settle for the menu
  for _ in $(seq 1 50); do real_game_up && break; sleep 2; done
  if real_game_up; then echo "game exe up; settling for menu..."; sleep 25; echo "READY"; else
    echo "GAME DID NOT START" >&2; return 1; fi
}

if command -v umu-run >/dev/null 2>&1; then
  # ---- umu backend: clean kill of just this instance's process tree ----
  echo "umu backend: restarting instance $INSTANCE_ID"
  pkill -9 -f "instance_${INSTANCE_ID}/" 2>/dev/null || true
  sleep 2
  PID="$("$SELF_DIR/launch_balatro.sh" "$INSTANCE_ID")"
  echo "launched pid $PID"
  wait_for_menu
  exit $?
fi

# ---- snap-Steam fallback (single instance) ----
echo "snap-Steam backend (umu-run not installed): single-instance restart"

# Kill the whole Balatro/Proton process group. Per-PID kill is resisted under the
# snap namespace; the group kill is reliable but also stops the Steam client.
ANY_PID="$(ps -eo pid,args | grep -iE 'AppId=2379780|steamapps/common/Balatro' \
            | grep -v grep | grep -v 'restart_balatro' | awk '{print $1; exit}')"
if [ -n "${ANY_PID:-}" ]; then
  PGID="$(ps -o pgid= -p "$ANY_PID" 2>/dev/null | tr -d ' ')"
  [ -n "$PGID" ] && { echo "killing process group $PGID (this also stops Steam)"; kill -9 -- -"$PGID" 2>/dev/null || true; }
  sleep 4
fi

# Restart Steam if it went down with the group kill.
if ! ps -eo args | grep -v grep | grep -qE 'ubuntu12_32/steam|steamwebhelper'; then
  echo "starting Steam..."; setsid steam >/dev/null 2>&1 < /dev/null &
  for _ in $(seq 1 40); do
    ps -eo args | grep -v grep | grep -qE 'steamwebhelper' && break; sleep 2
  done
  echo "Steam up; giving it 20s to finish login..."; sleep 20
fi

echo "launching Balatro via Steam..."
setsid steam "steam://rungameid/2379780" >/dev/null 2>&1 < /dev/null &
wait_for_menu
