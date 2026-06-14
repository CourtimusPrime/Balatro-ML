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
json = assert(SMODS.load_file("lib/json.lua"))()   -- expose json.encode / json.decode as a global (rxi/json.lua returns a local table)
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
local _pending_blind = nil              -- deferred blind action ("select_blind"/"skip_blind") awaiting a ready UI
local _awaiting_response = false         -- true after an action is dispatched, until its one snapshot is emitted
local _last_acted_on_deck = nil          -- blind_on_deck we last select/skipped; suppresses re-acting during teardown

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
    print("[BML] snapshot error on '" .. tostring(event_name) .. "': " .. tostring(payload))
    return   -- snapshot error; skip this emit rather than crashing
  end

  local ok_enc, encoded = pcall(json.encode, payload)
  if not ok_enc then
    print("[BML] json.encode error on '" .. tostring(event_name) .. "': " .. tostring(encoded))
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

  -- Retry any deferred blind-select action now that another frame has elapsed
  -- and the lazily-built blind-select UI may have become ready.
  BML_Bridge._try_blind()

  -- Emit the single snapshot owed for the in-flight action once the game has
  -- settled into a resting state (auto-advancing non-decision screens first).
  BML_Bridge._advance_and_respond()
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
-- BML_Bridge._current_blind_opt
-- ---------------------------------------------------------------------------
-- Returns the UIBox for the blind currently on deck (Small/Big/Boss) from
-- G.blind_select_opts, or nil when the blind-select screen isn't showing.
-- select_blind / skip_blind locate their button elements within this box.
function BML_Bridge._current_blind_opt()
  -- Require blind_on_deck to be set: it is assigned while the blind-select UI is
  -- built (UI_definitions.lua:1620), and G.FUNCS.select_blind indexes
  -- round_resets.blind_states[blind_on_deck] — a nil key would error. Returning
  -- nil until it is set lets _try_blind() keep waiting instead of acting early.
  if not (G.blind_select_opts and G.GAME and G.GAME.blind_on_deck) then return nil end
  local key = string.lower(tostring(G.GAME.blind_on_deck))
  return G.blind_select_opts[key]
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._blind_ready
-- ---------------------------------------------------------------------------
-- True when the blind-select screen is fully interactive: we're in BLIND_SELECT,
-- G.blind_select exists, blind_on_deck is set, the option box is found, and its
-- select button has been realised (the buttons build lazily). Used to decide when
-- to emit blind_start (a new decision is possible) and is exactly the condition
-- under which _try_blind can land an action — so the two never disagree.
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
-- Executes a deferred blind-select action once the UI is actually ready.
--
-- Why deferred: the blind-select option boxes (G.blind_select_opts.small/big/
-- boss) are built with UIBox_dyn_container (UI_definitions.lua:1623-1625), whose
-- children — the 'select_blind_button' and 'tag_container' elements — are
-- realised lazily, several frames after blind_start fires (with ~77 events still
-- queued). An action that arrives immediately therefore can't find its button.
-- So dispatch() stashes the action in _pending_blind and poll() calls this every
-- frame until get_UIE_by_ID succeeds, then fires it. Python's 5s step() timeout
-- bounds the wait; if the UI never becomes ready the episode truncates.
function BML_Bridge._try_blind()
  if not _pending_blind then return end

  -- Bail (without clearing) if we're not on a ready blind-select screen — e.g.
  -- mid-teardown or already advanced. start_run clears _pending_blind on reset.
  if not (G.STATE == G.STATES.BLIND_SELECT and G.blind_select
          and G.GAME and G.GAME.blind_on_deck) then
    return
  end

  local opt = BML_Bridge._current_blind_opt()
  if not opt then return end

  -- Record which blind we act on BEFORE firing (skip_blind mutates blind_on_deck
  -- synchronously). _last_acted_on_deck stops _advance_and_respond from re-emitting
  -- blind_start for this same blind during its deferred teardown.
  local acted = tostring(G.GAME.blind_on_deck)

  if _pending_blind == "select_blind" then
    -- select_blind(e) reads e.config.ref_table (the blind) and
    -- e.UIBox:get_UIE_by_ID('tag_container'); the button element supplies both.
    local btn = opt:get_UIE_by_ID("select_blind_button")
    if not btn then return end          -- dyn container not realised yet; retry next frame
    local ok, err = pcall(function() G.FUNCS.select_blind(btn) end)
    if not ok then print("[BML] select_blind error: " .. tostring(err)) end
    _last_acted_on_deck = acted
    _pending_blind = nil

  elseif _pending_blind == "skip_blind" then
    -- skip_blind(e) dereferences e.UIBox:get_UIE_by_ID('tag_container'); passing
    -- the tag_container element itself satisfies that (its .UIBox is the opt box).
    local tag = opt:get_UIE_by_ID("tag_container")
    if not tag then
      -- Boss blinds have no skip tag/button — fall back to selecting it so the
      -- agent never jams there. Small/Big always have a tag, so keep waiting for
      -- it to realise rather than mis-selecting.
      if acted == "Boss" then
        local btn = opt:get_UIE_by_ID("select_blind_button")
        if not btn then return end
        local ok, err = pcall(function() G.FUNCS.select_blind(btn) end)
        if not ok then print("[BML] boss select (skip fallback) error: " .. tostring(err)) end
        _last_acted_on_deck = acted
        _pending_blind = nil
      end
      return                            -- non-boss: tag not realised yet; retry
    end
    local ok, err = pcall(function() G.FUNCS.skip_blind(tag) end)
    if not ok then print("[BML] skip_blind error: " .. tostring(err)) end
    _last_acted_on_deck = acted
    _pending_blind = nil

  else
    _pending_blind = nil                -- unknown pending value; drop it
  end
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._classify_state
-- ---------------------------------------------------------------------------
-- Maps the current resting game state to the single event name Python expects.
-- Returns nil for intermediate/animating states (HAND_PLAYED, DRAW_TO_HAND,
-- ROUND_EVAL, NEW_ROUND, *_PACK, ...) so _advance_and_respond keeps waiting.
-- The returned names are all in the env's ACTIONABLE_EVENTS set, so no Python
-- change is needed — every action yields exactly one of these.
function BML_Bridge._classify_state()
  if not (G and G.STATE and G.STATES) then return nil end
  -- Terminal first: win sets G.GAME.won; loss drops to GAME_OVER.
  if G.GAME and G.GAME.won then return "run_win" end
  if G.STATE == G.STATES.GAME_OVER then return "run_lose" end
  -- Interactive resting states the agent acts in.
  if G.STATE == G.STATES.SHOP then return "shop_open" end
  if G.STATE == G.STATES.BLIND_SELECT then return "blind_start" end
  if G.STATE == G.STATES.SELECTING_HAND then return "draw" end
  return nil   -- intermediate/animating state — not ready to report yet
end

-- ---------------------------------------------------------------------------
-- BML_Bridge._advance_and_respond
-- ---------------------------------------------------------------------------
-- Strict 1-action -> 1-response: after dispatch() sets _awaiting_response, this
-- (called every poll) waits for the game to finish transitioning (G.STATE_COMPLETE)
-- then emits exactly one classified snapshot. It also auto-advances the cash-out
-- screen (ROUND_EVAL), which has no agent action — otherwise the agent would
-- stall there after beating a blind.
function BML_Bridge._advance_and_respond()
  if not _awaiting_response then return end
  if _pending_blind then return end          -- blind action not fired yet; wait

  -- Once we've left the blind-select screen, clear the "already acted" guard so
  -- the next ante's blind selection is allowed again.
  if G.STATE ~= G.STATES.BLIND_SELECT then _last_acted_on_deck = nil end

  -- Blind-select: emit blind_start ONLY when the screen is ready for a decision
  -- (buttons realised) AND it's a blind we haven't already acted on. Without the
  -- second check we'd re-emit during the deferred teardown after an action lands
  -- (G.blind_select still present for a few frames), making Python fire a second
  -- blind action into the half-built next screen and jam.
  if G.STATE == G.STATES.BLIND_SELECT then
    if BML_Bridge._blind_ready()
       and tostring(G.GAME.blind_on_deck) ~= _last_acted_on_deck then
      BML_Bridge.emit("blind_start")
      _awaiting_response = false
    end
    return                                    -- not ready / already acted → wait
  end

  if not G.STATE_COMPLETE then return end     -- mid-transition/animation; wait

  -- Auto-advance the post-blind cash-out screen to the shop. cash_out(e) does
  -- e.config.button = nil, so it needs a table with a .config field.
  if G.STATE == G.STATES.ROUND_EVAL then
    if G.round_eval then
      pcall(function() G.FUNCS.cash_out({ config = {} }) end)
    end
    return                                    -- wait for SHOP on a later poll
  end

  local ev = BML_Bridge._classify_state()
  if not ev then return end                   -- intermediate state; keep waiting
  BML_Bridge.emit(ev)
  _awaiting_response = false
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
      -- New episode: drop any blind action still waiting from a prior run so it
      -- can't fire into the fresh run after teardown.
      _pending_blind = nil
      _last_acted_on_deck = nil
      -- Run animations at max speed so scoring/shop transitions settle quickly
      -- (keeps each step() well inside its socket timeout, and speeds training).
      if G.SETTINGS then G.SETTINGS.GAMESPEED = 4 end
      -- Multi-game reset: if a run is already active (not at the main menu),
      -- tear it down first so start_run can set up a clean run.
      if G.STATE ~= G.STATES.MENU then
        pcall(function() G:delete_run() end)
      end
      -- Balatro's Game:start_run derives the deck from G.GAME.viewed_back.name
      -- (resolved via get_deck_from_name over G.P_CENTERS), NOT from an args
      -- field. Set viewed_back so the requested deck is honoured; if the key
      -- is unknown, start_run falls back to 'Red Deck'.
      local deck_key = action.deck or "b_red"
      local center = G.P_CENTERS and G.P_CENTERS[deck_key]
      if center and G.GAME then
        G.GAME.viewed_back = { name = center.name }
      end
      -- start_run is a method (function Game:start_run); call with ':' so
      -- self == G. Calling with '.' passes the args table as self and makes
      -- self:prep_stage() fail (game.lua:2055).
      G:start_run({ stake = action.stake or 1, seed = "" })

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
      -- Defer: the select button is realised lazily a few frames after
      -- blind_start (see BML_Bridge._try_blind). Stash it; poll() retries each
      -- frame until the button is findable, then calls G.FUNCS.select_blind.
      _pending_blind = "select_blind"
      BML_Bridge._try_blind()

    elseif name == "skip_blind" then
      -- Defer: same lazy-realisation reason as select_blind. poll() retries until
      -- the tag_container element exists, then calls G.FUNCS.skip_blind.
      _pending_blind = "skip_blind"
      BML_Bridge._try_blind()

    end
  end)
  -- ok=false: game function errored or name was wrong; silently absorbed.
  if not ok then
    print("[BML] dispatch error for '" .. tostring(name) .. "': " .. tostring(err))
  end

  -- Every dispatched game action owes Python exactly one snapshot. poll() ->
  -- _advance_and_respond() emits it once the resulting state settles. (Blind
  -- actions also set _pending_blind, which gates the response until they fire.)
  _awaiting_response = true
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
-- Emit model: poll-driven, one snapshot per action (NOT per-FUNCS hooks)
-- ---------------------------------------------------------------------------
-- Earlier revisions wrapped individual G.FUNCS (play_cards_from_highlighted,
-- discard_cards_from_highlighted, draw_from_deck_to_hand, toggle_shop,
-- buy_from_shop, cash_out, game_over) and G.start_run to emit an event per game
-- transition. That assumed one action -> one event, which is false: toggle_card
-- / skip_blind / reroll / sell / use emit nothing, while a single commit_play can
-- emit two (hand_played + a refill draw). Either way step() would time out or
-- desync. The hooks are removed; _advance_and_respond() (called from poll) now
-- emits exactly one classified snapshot once each action's resulting state
-- settles (G.STATE_COMPLETE), auto-advancing the no-decision cash-out screen.

-- ---------------------------------------------------------------------------
-- Initial connection attempt
-- ---------------------------------------------------------------------------
-- Called once at mod load time. If Python isn't running yet, poll() will
-- retry every frame automatically.
BML_Bridge.connect()
