-- mod/logic.lua — reloadable BML_Bridge logic (hot-reloaded via the "reload" action).
--
-- This file defines all BML_Bridge.* functions and is RE-RUNNABLE at runtime:
-- dispatch's "reload" branch re-loads it (and state.lua) so mod logic changes apply
-- in ~seconds without a 60-90s game restart. Therefore this file MUST NOT wrap
-- love.update or hold connection state in file-locals — both live in the persistent
-- `BML` table created once by the bridge.lua bootstrap (and never reset on reload).
--
-- love.update -> BML_Bridge.poll(dt) is wired once in bridge.lua by TABLE LOOKUP, so
-- redefining BML_Bridge.* here takes effect immediately after a reload.

BML_Bridge = BML_Bridge or {}

local socket = require("socket")   -- cached in package.loaded; safe to re-require on reload

-- ---------------------------------------------------------------------------
-- BML_Bridge.connect
-- ---------------------------------------------------------------------------
-- Creates a new non-blocking TCP client and attempts to connect to the Python
-- server. Non-blocking connect returns "timeout" immediately; the three-way
-- handshake completes within the next frame and subsequent sends succeed.
function BML_Bridge.connect()
  local ok, err
  BML.client = socket.tcp()
  BML.client:settimeout(0)                       -- non-blocking I/O
  BML.client:setoption("tcp-nodelay", true)      -- disable Nagle — low-latency sends
  ok, err = BML.client:connect(BML.host, BML.port)
  -- Non-blocking connect: ok=nil, err="timeout" on first call is normal.
  if ok or err == "timeout" then
    BML.connected = true
  else
    BML.connected = false   -- Python server not yet running; retry next poll
  end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge.emit / emit_raw
-- ---------------------------------------------------------------------------
function BML_Bridge.emit(event_name)
  if not BML.connected then return end

  local ok_snap, payload = pcall(BML_State.snapshot, event_name)
  if not ok_snap then
    print("[BML] snapshot error on '" .. tostring(event_name) .. "': " .. tostring(payload))
    return
  end

  local ok_enc, encoded = pcall(json.encode, payload)
  if not ok_enc then
    print("[BML] json.encode error on '" .. tostring(event_name) .. "': " .. tostring(encoded))
    return
  end

  local bytes = BML.client:send(encoded .. "\n")
  if not bytes then BML.connected = false end
end

function BML_Bridge.emit_raw(line)
  if not BML.connected then return end
  local bytes = BML.client:send(line)
  if not bytes then BML.connected = false end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge.poll — per-frame socket I/O (called from love.update via bridge.lua)
-- ---------------------------------------------------------------------------
function BML_Bridge.poll(dt)
  if not BML.connected then
    BML_Bridge.connect()
    return
  end

  -- Drain all available incoming lines (non-blocking; timeout=0 already set).
  while true do
    local line, err = BML.client:receive("*l")
    if line then
      local ok, action = pcall(json.decode, line)
      if ok and type(action) == "table" then
        BML_Bridge.dispatch(action)
      end
    else
      if err ~= "timeout" then BML.connected = false end
      break
    end
  end

  -- Retry any deferred blind-select action now that another frame has elapsed.
  BML_Bridge._try_blind()

  -- Emit the single snapshot owed for the in-flight action once settled.
  BML_Bridge._advance_and_respond()
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._get_all_shop_items
-- ---------------------------------------------------------------------------
-- Flattens G.shop_jokers, G.shop_vouchers, G.shop_booster into one 1-based list.
-- The "buy" action maps action.index+1 into this list.
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
-- BML_Bridge._current_blind_opt
-- ---------------------------------------------------------------------------
-- The option UIBox for the blind on deck. Requires blind_on_deck set, since
-- G.FUNCS.select_blind indexes round_resets.blind_states[blind_on_deck].
function BML_Bridge._current_blind_opt()
  if not (G.blind_select_opts and G.GAME and G.GAME.blind_on_deck) then return nil end
  local key = string.lower(tostring(G.GAME.blind_on_deck))
  return G.blind_select_opts[key]
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._blind_ready
-- ---------------------------------------------------------------------------
-- True when the blind-select screen is fully interactive (buttons realised).
function BML_Bridge._blind_ready()
  if not (G.STATE == G.STATES.BLIND_SELECT and G.blind_select
          and G.GAME and G.GAME.blind_on_deck) then
    return false
  end
  local opt = BML_Bridge._current_blind_opt()
  if not opt then return false end
  return opt:get_UIE_by_ID("select_blind_button") ~= nil
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._try_blind
-- ---------------------------------------------------------------------------
-- Fires a deferred blind action once the lazily-built UI is ready. The option
-- boxes use UIBox_dyn_container, whose select_blind_button / tag_container
-- children realise several frames after blind_start. We retry every poll until
-- get_UIE_by_ID succeeds. _last_acted_on_deck suppresses re-acting during teardown.
function BML_Bridge._try_blind()
  if not BML.pending_blind then return end

  if not (G.STATE == G.STATES.BLIND_SELECT and G.blind_select
          and G.GAME and G.GAME.blind_on_deck) then
    return
  end

  local opt = BML_Bridge._current_blind_opt()
  if not opt then return end

  -- Record the acted-on blind BEFORE firing (skip_blind mutates blind_on_deck).
  local acted = tostring(G.GAME.blind_on_deck)

  if BML.pending_blind == "select_blind" then
    local btn = opt:get_UIE_by_ID("select_blind_button")
    if not btn then return end          -- dyn container not realised yet; retry
    local ok, err = pcall(function() G.FUNCS.select_blind(btn) end)
    if not ok then print("[BML] select_blind error: " .. tostring(err)) end
    BML.last_acted_on_deck = acted
    BML.pending_blind = nil

  elseif BML.pending_blind == "skip_blind" then
    local tag = opt:get_UIE_by_ID("tag_container")
    if not tag then
      -- Boss has no skip tag — fall back to selecting it so the agent never jams.
      if acted == "Boss" then
        local btn = opt:get_UIE_by_ID("select_blind_button")
        if not btn then return end
        local ok, err = pcall(function() G.FUNCS.select_blind(btn) end)
        if not ok then print("[BML] boss select (skip fallback) error: " .. tostring(err)) end
        BML.last_acted_on_deck = acted
        BML.pending_blind = nil
      end
      return                            -- non-boss: tag not realised yet; retry
    end
    local ok, err = pcall(function() G.FUNCS.skip_blind(tag) end)
    if not ok then print("[BML] skip_blind error: " .. tostring(err)) end
    BML.last_acted_on_deck = acted
    BML.pending_blind = nil

  else
    BML.pending_blind = nil             -- unknown pending value; drop it
  end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._classify_state
-- ---------------------------------------------------------------------------
-- Maps the resting game state to the single event name Python expects, or nil
-- for intermediate/animating states (HAND_PLAYED, DRAW_TO_HAND, NEW_ROUND,
-- ROUND_EVAL) so _advance_and_respond keeps waiting. All returned names are in
-- the env's ACTIONABLE_EVENTS set.
function BML_Bridge._classify_state()
  if not (G and G.STATE and G.STATES) then return nil end
  if G.GAME and G.GAME.won then return "run_win" end
  if G.STATE == G.STATES.GAME_OVER then return "run_lose" end
  if G.STATE == G.STATES.SHOP then return "shop_open" end
  if G.STATE == G.STATES.BLIND_SELECT then return "blind_start" end
  if G.STATE == G.STATES.SELECTING_HAND then return "draw" end
  -- Booster-pack open: any *_PACK state is a resting decision state.
  local PACK_STATES = {}
  if G.STATES.TAROT_PACK    then PACK_STATES[G.STATES.TAROT_PACK]    = true end
  if G.STATES.PLANET_PACK   then PACK_STATES[G.STATES.PLANET_PACK]   = true end
  if G.STATES.SPECTRAL_PACK then PACK_STATES[G.STATES.SPECTRAL_PACK] = true end
  if G.STATES.STANDARD_PACK then PACK_STATES[G.STATES.STANDARD_PACK] = true end
  if G.STATES.BUFFOON_PACK  then PACK_STATES[G.STATES.BUFFOON_PACK]  = true end
  if PACK_STATES[G.STATE] then return "pack_open" end
  return nil   -- intermediate/animating state — not ready to report yet
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._advance_and_respond
-- ---------------------------------------------------------------------------
-- Strict 1-action -> 1-response: emit exactly one classified snapshot once the
-- action's resulting state settles (G.STATE_COMPLETE). Auto-advances the
-- no-decision cash-out screen (ROUND_EVAL).
function BML_Bridge._advance_and_respond()
  if not BML.awaiting_response then return end
  if BML.pending_blind then return end       -- blind action not fired yet; wait

  -- Clear the "already acted" guard once we've left the blind-select screen.
  if G.STATE ~= G.STATES.BLIND_SELECT then BML.last_acted_on_deck = nil end

  -- Blind-select: emit blind_start only when ready AND not a blind we just acted
  -- on (avoids a teardown feedback loop that jams the next screen).
  if G.STATE == G.STATES.BLIND_SELECT then
    if BML_Bridge._blind_ready()
       and tostring(G.GAME.blind_on_deck) ~= BML.last_acted_on_deck then
      BML_Bridge.emit("blind_start")
      BML.awaiting_response = false
    end
    return
  end

  if not G.STATE_COMPLETE then return end    -- mid-transition/animation; wait

  -- Auto-advance the post-blind cash-out screen to the shop.
  if G.STATE == G.STATES.ROUND_EVAL then
    if G.round_eval then
      pcall(function() G.FUNCS.cash_out({ config = {} }) end)
    end
    return                                   -- wait for SHOP on a later poll
  end

  local ev = BML_Bridge._classify_state()
  if not ev then return end                  -- intermediate state; keep waiting
  BML_Bridge.emit(ev)
  BML.awaiting_response = false
end

-- ---------------------------------------------------------------------------
-- BML_Bridge.dispatch — decode an action dict and call the matching G.FUNCS
-- ---------------------------------------------------------------------------
function BML_Bridge.dispatch(action)
  local name = action.action
  if not name then return end

  -- probe_funcs: enumerate G.FUNCS keys (diagnostic; no game mutation, no response).
  if name == "probe_funcs" then
    local keys = {}
    if G.FUNCS then for k, _ in pairs(G.FUNCS) do keys[#keys + 1] = k end end
    table.sort(keys)
    local ok_enc, encoded = pcall(json.encode, { event = "probe_funcs_result", funcs = keys })
    if ok_enc then BML_Bridge.emit_raw(encoded .. "\n") end
    return
  end

  -- reload: hot-reload mod logic (state.lua + logic.lua) without restarting the
  -- game. Redefines BML_State.* and BML_Bridge.* in place; connection and the
  -- persistent BML table survive. Not a game action, so no _awaiting_response.
  if name == "reload" then
    -- SMODS.load_file needs the mod id at runtime (SMODS.current_mod is only set
    -- during initial load; without an id it errors). Use the captured/known id.
    local mid = BML.mod_id or "BalatroML"
    local ok_s, err_s = pcall(function() assert(SMODS.load_file("state.lua", mid))() end)
    local ok_l, err_l = pcall(function() assert(SMODS.load_file("logic.lua", mid))() end)
    if ok_s and ok_l then
      BML_Bridge.emit_raw('{"event":"reload_ok"}\n')
    else
      print("[BML] reload error: state=" .. tostring(err_s) .. " logic=" .. tostring(err_l))
      BML_Bridge.emit_raw('{"event":"reload_error"}\n')
    end
    return
  end

  -- All game-mutation branches share one pcall: a bad action never crashes the
  -- game loop; Python's socket timeout -> truncated handles a missed response.
  local ok, err = pcall(function()  -- luacheck: ignore err

    if name == "start_run" then
      BML.pending_blind = nil
      BML.last_acted_on_deck = nil
      if G.SETTINGS then G.SETTINGS.GAMESPEED = 4 end
      -- Robust reset from ANY state: replicate the game's go_to_menu sequence
      -- (clear the event queue, delete the run, return to MENU) before start_run.
      -- Calling start_run from a mid-animation state otherwise fails to reach
      -- BLIND_SELECT. See functions/button_callbacks.lua G.FUNCS.go_to_menu.
      if G.STATE ~= G.STATES.MENU then
        if G.E_MANAGER and G.E_MANAGER.clear_queue then
          pcall(function() G.E_MANAGER:clear_queue() end)
        end
        pcall(function() G:delete_run() end)
        pcall(function() G:main_menu("game") end)
      end
      -- start_run derives the deck from G.GAME.viewed_back.name (not an args field).
      local deck_key = action.deck or "b_red"
      local center = G.P_CENTERS and G.P_CENTERS[deck_key]
      if center and G.GAME then
        G.GAME.viewed_back = { name = center.name }
      end
      -- Method call (':') so self == G; '.' would break self:prep_stage().
      G:start_run({ stake = action.stake or 1, seed = "" })

    elseif name == "toggle_card" then
      -- Use the real selection API so G.hand.highlighted (the list
      -- play_cards_from_highlighted reads) stays in sync. Setting card.highlighted
      -- directly leaves that list empty -> commit_play plays nothing -> Balatro's
      -- evaluate_play crashes indexing G.GAME.hands[nil] (state_events.lua:593).
      local i = action.index + 1
      local card = G.hand and G.hand.cards and G.hand.cards[i]
      if card then
        if card.highlighted then
          G.hand:remove_from_highlighted(card)
        else
          G.hand:add_to_highlighted(card)
        end
      end

    elseif name == "commit_play" then
      G.FUNCS.play_cards_from_highlighted({})

    elseif name == "commit_discard" then
      G.FUNCS.discard_cards_from_highlighted({})

    elseif name == "buy" then
      local i = action.index + 1
      local card = BML_Bridge._get_all_shop_items()[i]
      if card then G.FUNCS.buy_from_shop({ config = { ref_table = card } }) end

    elseif name == "sell_joker" then
      local i = action.index + 1
      local card = G.jokers and G.jokers.cards and G.jokers.cards[i]
      if card and card.ability and not card.ability.eternal then
        G.FUNCS.sell_card({ config = { ref_table = card } })
      end

    elseif name == "use_consumable" then
      -- Game ships with a typo — the consumable CardArea is G.consumeables.
      local i = action.index + 1
      local card = G.consumeables and G.consumeables.cards and G.consumeables.cards[i]
      if card then G.FUNCS.use_card({ config = { ref_table = card } }) end

    elseif name == "reroll" then
      G.FUNCS.reroll_shop({})

    elseif name == "leave_shop" then
      G.FUNCS.toggle_shop({})

    elseif name == "select_blind" then
      BML.pending_blind = "select_blind"
      BML_Bridge._try_blind()

    elseif name == "skip_blind" then
      BML.pending_blind = "skip_blind"
      BML_Bridge._try_blind()

    elseif name == "select_pack_card" then
      local i = action.index + 1
      local card = G.pack_cards and G.pack_cards.cards and G.pack_cards.cards[i]
      if card then
        card.highlighted = true
        G.FUNCS.use_card({ config = { ref_table = card } })
      end

    elseif name == "skip_pack" then
      G.FUNCS.skip_booster({})

    end
  end)
  if not ok then
    print("[BML] dispatch error for '" .. tostring(name) .. "': " .. tostring(err))
  end

  -- Every dispatched game action owes Python exactly one snapshot.
  BML.awaiting_response = true
end
