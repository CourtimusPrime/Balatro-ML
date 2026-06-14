-- mod/bridge.lua  (main_file for Steamodded mod "BalatroML") — THIN BOOTSTRAP.
--
-- Loaded ONCE at game launch and never re-run. Responsibilities that must happen
-- exactly once live here; all reloadable logic lives in logic.lua.
--   1. Load deps (lib/json.lua -> global json, state.lua -> global BML_State).
--   2. Create the persistent `BML` state table (TCP client, connection flag, port,
--      and the action/blind bookkeeping). This survives logic.lua hot-reloads.
--   3. Load logic.lua, which defines BML_Bridge.* (connect/poll/dispatch/...).
--   4. Wrap love.update ONCE to call BML_Bridge.poll(dt) BY TABLE LOOKUP, so a
--      reloaded logic.lua takes effect without re-wrapping love.update.
--   5. Open the initial connection.
--
-- Hot reload: dispatch's "reload" action re-runs state.lua + logic.lua, redefining
-- BML_State.* / BML_Bridge.* in place. bridge.lua is NOT re-run, so the love.update
-- wrapper and BML state are preserved. This turns a 60-90s game restart into a
-- ~seconds reload during mod development.

-- ---------------------------------------------------------------------------
-- 1. Dependencies (globals)
-- ---------------------------------------------------------------------------
json = assert(SMODS.load_file("lib/json.lua"))()   -- json.encode / json.decode
assert(SMODS.load_file("state.lua"))()             -- BML_State.snapshot()

-- ---------------------------------------------------------------------------
-- 2. Persistent state (survives logic.lua reloads)
-- ---------------------------------------------------------------------------
-- Guarded so a stray re-run of this file would not wipe a live connection.
-- Port is per-instance via BALATRO_ML_PORT (defaults to 12345) so multiple
-- Balatro instances can run in parallel, each bridged to its own trainer.
BML = BML or {
  client             = nil,
  connected          = false,
  host               = "127.0.0.1",
  port               = tonumber(os.getenv("BALATRO_ML_PORT")) or 12345,
  pending_blind      = nil,    -- deferred "select_blind"/"skip_blind" awaiting a ready UI
  awaiting_response  = false,  -- true after an action is dispatched, until its snapshot is emitted
  last_acted_on_deck = nil,    -- blind_on_deck we last acted on; suppresses re-acting during teardown
  debug_states       = true,   -- TEMP (W4): emit throttled DBG_STATE while awaiting a response
  dbg_tick           = 0,
}

-- ---------------------------------------------------------------------------
-- 3. Reloadable logic (defines BML_Bridge.*)
-- ---------------------------------------------------------------------------
assert(SMODS.load_file("logic.lua"))()

-- ---------------------------------------------------------------------------
-- 4. love.update hook — wrapped ONCE; calls BML_Bridge.poll by table lookup
-- ---------------------------------------------------------------------------
local _love_update = love.update
love.update = function(dt)
  _love_update(dt)
  if BML_Bridge and BML_Bridge.poll then
    BML_Bridge.poll(dt)
  end
end

-- ---------------------------------------------------------------------------
-- 5. Initial connection attempt (poll() retries every frame if Python isn't up)
-- ---------------------------------------------------------------------------
if BML_Bridge and BML_Bridge.connect then
  BML_Bridge.connect()
end
