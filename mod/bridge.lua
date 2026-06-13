-- mod/bridge.lua  (main_file for Steamodded mod "BalatroML")
-- BML_Bridge module: TCP client (luasocket), event hooks, SMODS file loading.
-- Connects to the Python SocketBridge server on 127.0.0.1:12345 and emits a
-- full game-state snapshot as newline-delimited JSON on each of 9 game events:
--   draw, hand_played, discard, blind_start, shop_open, shop_buy, shop_close,
--   run_win, run_lose
--
-- Dependencies (loaded first via SMODS.load_file):
--   mod/lib/json.lua  — vendored rxi/json.lua; exposes json.encode / json.decode
--   mod/state.lua     — BML_State module; exposes BML_State.snapshot()

-- ---------------------------------------------------------------------------
-- Load dependencies
-- ---------------------------------------------------------------------------
assert(SMODS.load_file("lib/json.lua"))()   -- json.encode / json.decode become global
assert(SMODS.load_file("state.lua"))()      -- BML_State.snapshot() becomes global

-- ---------------------------------------------------------------------------
-- Module state
-- ---------------------------------------------------------------------------
BML_Bridge = {}

local socket = require("socket")

local _client    = nil
local _connected = false
local HOST       = "127.0.0.1"
local PORT       = 12345
local _first_blind_start_done = false   -- tracks whether we've emitted debug_hand_names

-- ---------------------------------------------------------------------------
-- BML_Bridge.connect
-- ---------------------------------------------------------------------------
-- Creates a new non-blocking TCP client and attempts to connect to the Python
-- server. Non-blocking connect returns "timeout" immediately; the three-way
-- handshake completes within the next frame and subsequent sends succeed.
function BML_Bridge.connect()
  local ok, err
  _client = socket.tcp()
  _client:settimeout(0)                       -- non-blocking I/O
  _client:setoption("tcp-nodelay", true)      -- disable Nagle — low-latency sends
  ok, err = _client:connect(HOST, PORT)
  -- Non-blocking connect: ok=nil, err="timeout" on first call is normal.
  if ok or err == "timeout" then
    _connected = true
  else
    -- Python server not yet running; we'll retry next poll.
    _connected = false
  end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge.emit
-- ---------------------------------------------------------------------------
-- Serialises the current game state snapshot to JSON and sends it over the
-- TCP socket. If the send fails (Python server crashed, disconnected, etc.)
-- sets _connected=false so poll() will reconnect next frame.
function BML_Bridge.emit(event_name)
  if not _connected then return end

  local ok_snap, payload = pcall(BML_State.snapshot, event_name)
  if not ok_snap then
    return   -- snapshot error; skip this emit rather than crashing
  end

  local ok_enc, encoded = pcall(json.encode, payload)
  if not ok_enc then
    return   -- encode error; skip
  end

  local bytes, err = _client:send(encoded .. "\n")
  if not bytes then
    _connected = false   -- reconnect next poll
  end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge.emit_raw
-- ---------------------------------------------------------------------------
-- Sends a pre-encoded, newline-terminated string directly over _client without
-- going through json.encode. Used by the probe_funcs branch of dispatch() so
-- the response event can be built with json.encode before calling emit_raw.
function BML_Bridge.emit_raw(line)
  if not _connected then return end
  local bytes, err = _client:send(line)
  if not bytes then
    _connected = false
  end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge.poll
-- ---------------------------------------------------------------------------
-- Called every frame via the love.update wrapper.
-- Reconnects if disconnected; drains any incoming action messages from Python.
function BML_Bridge.poll(dt)
  if not _connected then
    BML_Bridge.connect()
    return
  end

  -- Drain all available incoming lines (non-blocking; timeout=0 already set).
  while true do
    local line, err = _client:receive("*l")
    if line then
      local ok, action = pcall(json.decode, line)
      if ok and type(action) == "table" then
        BML_Bridge.dispatch(action)
      end
    else
      -- err == "timeout" means no more data; any other error = disconnection.
      if err ~= "timeout" then
        _connected = false
      end
      break
    end
  end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._get_all_shop_items
-- ---------------------------------------------------------------------------
-- Flattens G.shop_jokers, G.shop_vouchers, and G.shop_booster into a single
-- ordered list. Python uses 0-based indices; this returns a 1-based Lua table.
-- The "buy" action from Python maps action.index+1 into this list.
function BML_Bridge._get_all_shop_items()
  local items = {}
  local areas = { G.shop_jokers, G.shop_vouchers, G.shop_booster }
  for _, area in ipairs(areas) do
    if area and area.cards then
      for i = 1, #area.cards do
        items[#items + 1] = area.cards[i]
      end
    end
  end
  return items
end

-- ---------------------------------------------------------------------------
-- BML_Bridge.dispatch
-- ---------------------------------------------------------------------------
-- Decodes an action dict (already json.decode'd in poll) and calls the
-- appropriate Balatro G.FUNCS or G.* entry point. All game mutations are
-- wrapped in a single top-level pcall so a bad action never crashes the game
-- loop. Python-side: socket timeout → truncated=True handles missed actions.
--
-- Verified G.FUNCS names (from Phase 1 bridge.lua hooks):
--   play_cards_from_highlighted, discard_cards_from_highlighted,
--   buy_from_shop, toggle_shop, cash_out, game_over
--
-- ASSUMED G.FUNCS names (not yet live-verified — run probe_lua_funcs.py):
--   sell_card     (sell_joker branch)    — ASSUMED, verify via probe_lua_funcs.py (02-04 checkpoint)
--   use_card      (use_consumable branch) — ASSUMED, verify via probe_lua_funcs.py (02-04 checkpoint)
--   reroll_shop   (reroll branch)        — ASSUMED, verify via probe_lua_funcs.py (02-04 checkpoint)
--   select_blind  (select_blind branch)  — ASSUMED, verify via probe_lua_funcs.py (02-04 checkpoint)
--   skip_blind    (skip_blind branch)    — ASSUMED, verify via probe_lua_funcs.py (02-04 checkpoint)
function BML_Bridge.dispatch(action)
  local name = action.action
  if not name then return end

  -- probe_funcs: collect all G.FUNCS keys and emit them over the socket.
  -- This branch does NOT go through the game-mutation pcall below; it only
  -- reads G.FUNCS and sends data, which is safe outside pcall.
  if name == "probe_funcs" then
    local keys = {}
    if G.FUNCS then
      for k, _ in pairs(G.FUNCS) do keys[#keys + 1] = k end
    end
    table.sort(keys)
    local ok_enc, encoded = pcall(json.encode, { event = "probe_funcs_result", funcs = keys })
    if ok_enc then
      BML_Bridge.emit_raw(encoded .. "\n")
    end
    return
  end

  -- All game-mutation branches are wrapped in a single pcall.
  -- If G.FUNCS name is wrong or the game is in an unexpected state the error
  -- is silently absorbed; Python will time out and set truncated=True.
  local ok, err = pcall(function()  -- luacheck: ignore err

    if name == "start_run" then
      -- Guard: only valid when the main menu is showing.
      if G.STATE == G.STATES.MENU then
        G.start_run({
          ante       = 1,
          final_ante = 8,
          seed       = "",
          stake      = action.stake or 1,
          challenge  = nil,
          deck       = { config = { center_key = action.deck or "b_red" } },
        })
      end

    elseif name == "toggle_card" then
      -- Python sends 0-based index; Lua cards table is 1-based.
      local i = action.index + 1
      local card = G.hand and G.hand.cards and G.hand.cards[i]
      if card then
        card.highlighted = not card.highlighted
      end

    elseif name == "commit_play" then
      G.FUNCS.play_cards_from_highlighted({})

    elseif name == "commit_discard" then
      G.FUNCS.discard_cards_from_highlighted({})

    elseif name == "buy" then
      local i = action.index + 1
      local all_items = BML_Bridge._get_all_shop_items()
      local card = all_items[i]
      if card then
        G.FUNCS.buy_from_shop({ config = { ref_table = card } })
      end

    elseif name == "sell_joker" then
      local i = action.index + 1
      local card = G.jokers and G.jokers.cards and G.jokers.cards[i]
      if card and card.ability and not card.ability.eternal then
        -- ASSUMED: G.FUNCS.sell_card — verify via probe_lua_funcs.py (02-04 checkpoint)
        G.FUNCS.sell_card({ config = { ref_table = card } })
      end

    elseif name == "use_consumable" then
      local i = action.index + 1
      -- Note: game ships with a typo — consumables CardArea is G.consumeables (extra 'e').
      local card = G.consumeables and G.consumeables.cards and G.consumeables.cards[i]
      if card then
        -- ASSUMED: G.FUNCS.use_card — verify via probe_lua_funcs.py (02-04 checkpoint)
        G.FUNCS.use_card({ config = { ref_table = card } })
      end

    elseif name == "reroll" then
      -- ASSUMED: G.FUNCS.reroll_shop — verify via probe_lua_funcs.py (02-04 checkpoint)
      G.FUNCS.reroll_shop({})

    elseif name == "leave_shop" then
      G.FUNCS.toggle_shop({})

    elseif name == "select_blind" then
      -- ASSUMED: G.FUNCS.select_blind — verify via probe_lua_funcs.py (02-04 checkpoint)
      G.FUNCS.select_blind({})

    elseif name == "skip_blind" then
      -- ASSUMED: G.FUNCS.skip_blind — verify via probe_lua_funcs.py (02-04 checkpoint)
      G.FUNCS.skip_blind({})

    end
  end)
  -- ok=false: game function errored or name was wrong; silently absorbed.
end

-- ---------------------------------------------------------------------------
-- love.update hook — per-frame socket I/O
-- ---------------------------------------------------------------------------
local _love_update = love.update
love.update = function(dt)
  _love_update(dt)
  BML_Bridge.poll(dt)
end

-- ---------------------------------------------------------------------------
-- Event hook: blind_start — G.start_run
-- ---------------------------------------------------------------------------
-- Emits when a new run begins (first blind of the run).
-- On first emit only, state.lua includes debug_hand_names to capture live
-- G.GAME.hands key strings during BRIDGE-05 verification.
local _start_run = G.start_run
G.start_run = function(args)
  _start_run(args)
  BML_Bridge.emit("blind_start")
end

-- ---------------------------------------------------------------------------
-- Event hook: hand_played — G.FUNCS.play_cards_from_highlighted
-- ---------------------------------------------------------------------------
-- Deferred via G.E_MANAGER (delay=0.1s) so scoring animations can settle
-- before we snapshot. Emits only when the event queue has < 3 pending items
-- (state-stability check from coder/balatrobot pattern).
local _play_orig = G.FUNCS.play_cards_from_highlighted
G.FUNCS.play_cards_from_highlighted = function(e)
  _play_orig(e)
  G.E_MANAGER:add_event(Event({
    trigger  = "after",
    delay    = 0.1,
    blocking = false,
    func     = function()
      if #G.E_MANAGER.queues.base <= 3 then
        BML_Bridge.emit("hand_played")
      end
      return true
    end
  }))
end

-- ---------------------------------------------------------------------------
-- Event hook: discard — G.FUNCS.discard_cards_from_highlighted
-- ---------------------------------------------------------------------------
-- Same deferred-emit pattern as hand_played to avoid mid-animation state.
local _discard_orig = G.FUNCS.discard_cards_from_highlighted
G.FUNCS.discard_cards_from_highlighted = function(e)
  _discard_orig(e)
  G.E_MANAGER:add_event(Event({
    trigger  = "after",
    delay    = 0.1,
    blocking = false,
    func     = function()
      if #G.E_MANAGER.queues.base <= 3 then
        BML_Bridge.emit("discard")
      end
      return true
    end
  }))
end

-- ---------------------------------------------------------------------------
-- Event hook: draw — G.GAME.blind.drawn_to_hand
-- ---------------------------------------------------------------------------
-- Wrapped after G.start_run sets up blind so the field is populated.
-- We re-wrap inside G.start_run to ensure it hooks the current round's function.
local _start_run_for_draw = G.start_run
G.start_run = function(args)
  _start_run_for_draw(args)
  -- Hook drawn_to_hand for the current blind object.
  if G.GAME and G.GAME.blind and type(G.GAME.blind.drawn_to_hand) == "function" then
    local _drawn_orig = G.GAME.blind.drawn_to_hand
    G.GAME.blind.drawn_to_hand = function(self, ...)
      local result = _drawn_orig(self, ...)
      BML_Bridge.emit("draw")
      return result
    end
  end
end

-- ---------------------------------------------------------------------------
-- Event hook: shop_open and shop_close — G.FUNCS.toggle_shop
-- ---------------------------------------------------------------------------
-- toggle_shop is called for both open and close; we discriminate using G.STATE.
local _toggle_shop_orig = G.FUNCS.toggle_shop
G.FUNCS.toggle_shop = function(e)
  local was_in_shop = (G.STATE == G.STATES.SHOP)
  _toggle_shop_orig(e)
  if was_in_shop then
    BML_Bridge.emit("shop_close")
  else
    BML_Bridge.emit("shop_open")
  end
end

-- ---------------------------------------------------------------------------
-- Event hook: shop_buy — G.FUNCS.buy_from_shop
-- ---------------------------------------------------------------------------
local _buy_orig = G.FUNCS.buy_from_shop
G.FUNCS.buy_from_shop = function(e)
  _buy_orig(e)
  BML_Bridge.emit("shop_buy")
end

-- ---------------------------------------------------------------------------
-- Event hook: run_win and run_lose — G.FUNCS.cash_out / game_over
-- ---------------------------------------------------------------------------
-- cash_out is called after the final blind is beaten; emit run_win if G.GAME.won.
-- game_over is called when the player loses; emit run_lose.

if G.FUNCS.cash_out then
  local _cash_out_orig = G.FUNCS.cash_out
  G.FUNCS.cash_out = function(e)
    _cash_out_orig(e)
    if G.GAME and G.GAME.won then
      BML_Bridge.emit("run_win")
    end
  end
end

if G.FUNCS.game_over then
  local _game_over_orig = G.FUNCS.game_over
  G.FUNCS.game_over = function(e)
    _game_over_orig(e)
    if not (G.GAME and G.GAME.won) then
      BML_Bridge.emit("run_lose")
    end
  end
end

-- ---------------------------------------------------------------------------
-- Initial connection attempt
-- ---------------------------------------------------------------------------
-- Called once at mod load time. If Python isn't running yet, poll() will
-- retry every frame automatically.
BML_Bridge.connect()
