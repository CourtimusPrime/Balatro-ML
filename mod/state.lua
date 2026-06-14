-- mod/state.lua
-- BML_State module: extracts G.* game state and returns a structured Lua table
-- matching the README observation schema. Loaded by bridge.lua via SMODS.load_file.
--
-- Field paths confirmed from:
--   coder/balatrobot src/lua/utils/gamestate.lua
--   besteon/balatrobot src/utils.lua
-- Note: the game ships with a typo — the consumable CardArea is G.consumeables (extra 'e').

BML_State = {}

-- ---------------------------------------------------------------------------
-- Private helpers
-- ---------------------------------------------------------------------------

-- card_to_table: convert a playing card object to a plain Lua table.
-- in_hand: bool — card is currently in the hand CardArea
-- in_deck: bool — card is in the remaining deck CardArea
local function card_to_table(card, in_hand, in_deck)
  local suit  = (card.config and card.config.card and card.config.card.suit)  or ""
  local value = (card.config and card.config.card and card.config.card.value) or ""
  local enhancement = (card.ability and card.ability.effect) or "Base"
  local edition     = (card.edition and card.edition.type)   or ""
  local seal        = card.seal or ""
  local debuffed    = card.debuff or false
  local selected    = card.highlighted or false
  return {
    suit        = suit,
    value       = value,
    enhancement = enhancement,
    edition     = edition,
    seal        = seal,
    debuffed    = debuffed,
    selected    = selected,
    in_hand     = in_hand,
    in_deck     = in_deck,
  }
end

-- joker_to_table: convert a joker card object to a plain Lua table.
-- index: 1-based position in G.jokers.cards (used for Blueprint target computation)
-- all_jokers: the full G.jokers.cards table for adjacent-slot lookups
local function joker_to_table(card, index, all_jokers)
  local id      = (card.config and card.config.center_key) or ""
  local edition = (card.edition and card.edition.type)     or ""
  local eternal    = (card.ability and card.ability.eternal)   or false
  local rental     = (card.ability and card.ability.rental)    or false
  local sell_value = card.sell_cost or 0

  -- perishable: true when perish_tally > 0 (rounds remaining)
  local perishable = false
  if card.ability and (card.ability.perish_tally or 0) > 0 then
    perishable = true
  end

  -- counter: first numeric value in card.ability.extra (0.0 if none)
  local counter = 0.0
  if card.ability and card.ability.extra then
    for _, v in pairs(card.ability.extra) do
      if type(v) == "number" then
        counter = v
        break
      end
    end
  end

  -- target_id: joker being copied by Blueprint or Brainstorm
  -- Blueprint (j_blueprint): copies the joker immediately to its right (index+1)
  -- Brainstorm (j_brainstorm): copies the leftmost joker (index 1)
  local target_id = ""
  if id == "j_blueprint" then
    local right = all_jokers and all_jokers[index + 1]
    if right then
      target_id = (right.config and right.config.center_key) or ""
    end
  elseif id == "j_brainstorm" then
    local first = all_jokers and all_jokers[1]
    if first and index ~= 1 then
      target_id = (first.config and first.config.center_key) or ""
    end
  end

  return {
    id          = id,
    edition     = edition,
    eternal     = eternal,
    perishable  = perishable,
    rental      = rental,
    sell_value  = sell_value,
    counter     = counter,
    target_id   = target_id,
  }
end

-- get_phase: map G.STATE numeric constant to a README phase string.
local function get_phase()
  if not G or not G.STATE or not G.STATES then
    return "playing"
  end
  if G.STATE == G.STATES.SELECTING_HAND then
    return "playing"
  elseif G.STATE == G.STATES.SHOP then
    return "shop"
  elseif G.STATE == G.STATES.BLIND_SELECT then
    return "blind_select"
  end
  -- Booster-pack phase: any of the five *_PACK states is a resting decision.
  -- Nil-guarded: if a PACK constant doesn't exist yet the table miss returns nil
  -- (falsy), so no error — just falls through to the "playing" default.
  local PACK_STATES = {}
  if G.STATES.TAROT_PACK    then PACK_STATES[G.STATES.TAROT_PACK]    = true end
  if G.STATES.PLANET_PACK   then PACK_STATES[G.STATES.PLANET_PACK]   = true end
  if G.STATES.SPECTRAL_PACK then PACK_STATES[G.STATES.SPECTRAL_PACK] = true end
  if G.STATES.STANDARD_PACK then PACK_STATES[G.STATES.STANDARD_PACK] = true end
  if G.STATES.BUFFOON_PACK  then PACK_STATES[G.STATES.BUFFOON_PACK]  = true end
  if PACK_STATES[G.STATE] then return "booster_pack" end
  return "playing"
end

-- get_blind_index: derive 0=small, 1=big, 2=boss from blind_states table.
local function get_blind_index()
  if not (G.GAME and G.GAME.round_resets and G.GAME.round_resets.blind_states) then
    return 0
  end
  local bs = G.GAME.round_resets.blind_states
  if bs.Boss == "Defeated" or bs.Boss == "Current" then
    return 2
  elseif bs.Big == "Defeated" or bs.Big == "Current" then
    return 1
  end
  return 0
end

-- get_blind_name: resolve the current boss blind's display name.
local function get_blind_name()
  if not (G.GAME and G.GAME.round_resets and G.GAME.round_resets.blind_choices) then
    return ""
  end
  local key = G.GAME.round_resets.blind_choices.Boss
  if key and G.P_BLINDS and G.P_BLINDS[key] then
    return G.P_BLINDS[key].name or ""
  end
  return ""
end

-- ---------------------------------------------------------------------------
-- Public API
-- ---------------------------------------------------------------------------

-- BML_State.snapshot(event_name)
-- Returns a complete observation table for the current game state.
-- event_name: one of "draw","hand_played","discard","blind_start","shop_open",
--             "shop_buy","shop_close","run_win","run_lose"
function BML_State.snapshot(event_name)
  local obs = {}

  -- Cards: all playing cards (hand + remaining deck)
  -- Sequential indexing (obs.cards[#obs.cards + 1] = ...) prevents sparse arrays
  -- which would encode as JSON objects instead of arrays.
  obs.cards = {}
  if G.hand and G.hand.cards then
    for i = 1, #G.hand.cards do
      obs.cards[#obs.cards + 1] = card_to_table(G.hand.cards[i], true, false)
    end
  end
  if G.deck and G.deck.cards then
    for i = 1, #G.deck.cards do
      obs.cards[#obs.cards + 1] = card_to_table(G.deck.cards[i], false, true)
    end
  end

  -- Jokers: pass full array for Blueprint/Brainstorm target_id computation
  obs.jokers = {}
  if G.jokers and G.jokers.cards then
    local all_jokers = G.jokers.cards
    for i = 1, #all_jokers do
      obs.jokers[#obs.jokers + 1] = joker_to_table(all_jokers[i], i, all_jokers)
    end
  end

  -- Consumables (note: game ships with typo G.consumeables — extra 'e')
  obs.consumables = {}
  if G.consumeables and G.consumeables.cards then
    for i = 1, #G.consumeables.cards do
      local card = G.consumeables.cards[i]
      obs.consumables[#obs.consumables + 1] = {
        id   = (card.config and card.config.center_key) or "",
        type = (card.ability and card.ability.set)      or "",
      }
    end
  end

  -- Shop items (populated during shop phase; empty arrays during playing phase)
  obs.shop = {}
  obs.shop.items = {}
  local shop_areas = {
    { area = G.shop_jokers,   set_default = "Joker"   },
    { area = G.shop_vouchers, set_default = "Voucher" },
    { area = G.shop_booster,  set_default = "Booster" },
  }
  for _, entry in ipairs(shop_areas) do
    local area = entry.area
    if area and area.cards then
      for i = 1, #area.cards do
        local c = area.cards[i]
        local center_key = ""
        if c.config then
          center_key = c.config.center_key or c.config.card_key or ""
        end
        local item_set = (c.ability and c.ability.set) or entry.set_default
        obs.shop.items[#obs.shop.items + 1] = {
          type        = item_set,
          id          = center_key,
          cost        = c.cost or 0,
          edition     = (c.edition and c.edition.type) or "",
          enhancement = (c.ability and c.ability.effect) or "",
          seal        = c.seal or "",
        }
      end
    end
  end
  obs.shop.reroll_cost =
    (G.GAME and G.GAME.current_round and G.GAME.current_round.reroll_cost) or 0

  -- Pack cards (offered cards when a booster pack is open).
  -- Always emitted (empty array when no pack open) so Python's defaulted
  -- obs.pack field always receives an array regardless of phase.
  -- [CITED: Steamodded G wiki — "G.pack_cards: Area for cards in a booster";
  --  besteon/balatrobot utils.lua extract_area(G.pack_cards) when not REMOVED]
  obs.pack = {}
  if G.pack_cards and G.pack_cards.cards and not G.pack_cards.REMOVED then
    for i = 1, #G.pack_cards.cards do
      local c = G.pack_cards.cards[i]
      local center_key = (c.config and (c.config.center_key or c.config.card_key)) or ""
      obs.pack[#obs.pack + 1] = {
        type        = (c.ability and c.ability.set) or "Base",
        id          = center_key,
        cost        = c.cost or 0,
        edition     = (c.edition and c.edition.type) or "",
        enhancement = (c.ability and c.ability.effect) or "",
        seal        = c.seal or "",
      }
    end
  end

  -- Game state scalars
  local gs = {}
  gs.ante               = (G.GAME and G.GAME.round_resets and G.GAME.round_resets.ante) or 0
  gs.blind              = get_blind_index()
  gs.blind_name         = get_blind_name()
  gs.chips_needed       = (G.GAME and G.GAME.blind and G.GAME.blind.chips) or 0
  gs.chips_scored       = (G.GAME and G.GAME.chips) or 0
  gs.hands_remaining    = (G.GAME and G.GAME.current_round and G.GAME.current_round.hands_left) or 0
  gs.discards_remaining = (G.GAME and G.GAME.current_round and G.GAME.current_round.discards_left) or 0
  gs.money              = (G.GAME and G.GAME.dollars) or 0
  gs.hand_size          = (G.hand and G.hand.config and G.hand.config.card_limit) or 0
  gs.joker_slots        = (G.GAME and G.GAME.max_jokers) or 0
  gs.consumable_slots   =
    (G.consumeables and G.consumeables.config and G.consumeables.config.card_limit) or 0
  gs.reroll_cost        =
    (G.GAME and G.GAME.current_round and G.GAME.current_round.reroll_cost) or 0

  -- Pack scalars (0 / "" when no pack open; always emitted so Python defaults match).
  -- [ASSUMED: G.GAME.pack_choices is the remaining-pick counter decremented per pick.
  --  Verify via probe_lua_funcs.py (02-04 checkpoint). Could also be derived from
  --  G.GAME.pack_size if pack_choices is absent.]
  gs.pack_picks_remaining = (G.GAME and G.GAME.pack_choices) or 0

  -- Derive pack_type string from G.STATE so Python can normalise via PACK_TYPE_MAP.
  -- [CITED: G.STATES.TAROT_PACK / PLANET_PACK / SPECTRAL_PACK exist (can_use checks);
  --  STANDARD_PACK / BUFFOON_PACK by the same pattern — ASSUMED: verify via probe.]
  local PACK_TYPE_BY_STATE = {}
  if G.STATES then
    if G.STATES.TAROT_PACK    then PACK_TYPE_BY_STATE[G.STATES.TAROT_PACK]    = "Arcana"    end
    if G.STATES.PLANET_PACK   then PACK_TYPE_BY_STATE[G.STATES.PLANET_PACK]   = "Celestial" end
    if G.STATES.STANDARD_PACK then PACK_TYPE_BY_STATE[G.STATES.STANDARD_PACK] = "Standard"  end
    if G.STATES.BUFFOON_PACK  then PACK_TYPE_BY_STATE[G.STATES.BUFFOON_PACK]  = "Buffoon"   end
    if G.STATES.SPECTRAL_PACK then PACK_TYPE_BY_STATE[G.STATES.SPECTRAL_PACK] = "Spectral"  end
  end
  gs.pack_type = (G.STATE and PACK_TYPE_BY_STATE[G.STATE]) or ""

  -- hand_levels: dict keyed by hand name string (e.g. "High Card")
  gs.hand_levels = {}
  if G.GAME and G.GAME.hands then
    for name, h in pairs(G.GAME.hands) do
      gs.hand_levels[name] = h.level or 1
    end
  end

  -- last_hand: the scored poker hand, emitted ONLY on a hand_played event so
  -- the dashboard's best-run hand-by-hand (Panel 5) and hand-type-frequency
  -- (Panel 6) panels have real data (03-RESEARCH Pitfall 4 option b). Omitted
  -- (nil -> JSON null / absent) for every other event; observation.py defaults
  -- FullObservation.last_hand to None.
  -- Every G.* access is nil-guarded exactly like the surrounding code so a
  -- missing global degrades to a default rather than erroring.
  if event_name == "hand_played" then
    -- Poker hand name: the most-recently-scored hand type.
    -- [ASSUMED: G.GAME.last_hand_played holds the scored poker hand key on a
    --  hand_played event. verify via reload_mod.py during 03-04 live seed.]
    local hand_type = (G.GAME and G.GAME.last_hand_played) or ""
    -- Fallback: G.GAME.current_round.current_hand.handname (the round's current
    -- displayed hand) when last_hand_played is absent.
    -- [ASSUMED: current_round.current_hand.handname; verify at 03-04.]
    if hand_type == "" and G.GAME and G.GAME.current_round
        and G.GAME.current_round.current_hand then
      hand_type = G.GAME.current_round.current_hand.handname or ""
    end

    -- Per-hand chips + mult from the round's current_hand scratch fields.
    -- [ASSUMED: G.GAME.current_round.current_hand.chips / .mult carry the
    --  per-hand chips and mult; verify via reload_mod.py during 03-04 live seed.]
    local hand_chips = 0
    local hand_mult  = 0
    if G.GAME and G.GAME.current_round and G.GAME.current_round.current_hand then
      hand_chips = G.GAME.current_round.current_hand.chips or 0
      hand_mult  = G.GAME.current_round.current_hand.mult  or 0
    end

    -- n_cards: number of cards in the played/highlighted hand.
    -- [ASSUMED: G.play.cards holds the just-played cards on hand_played;
    --  fallback to highlighted hand cards. verify at 03-04.]
    local n_cards = 0
    if G.play and G.play.cards then
      n_cards = #G.play.cards
    elseif G.hand and G.hand.cards then
      for i = 1, #G.hand.cards do
        if G.hand.cards[i].highlighted then
          n_cards = n_cards + 1
        end
      end
    end

    obs.last_hand = {
      hand_type = hand_type,
      chips     = hand_chips,
      mult      = hand_mult,
      n_cards   = n_cards,
    }
  end

  obs.game_state = gs
  obs.phase      = get_phase()
  obs.event      = event_name

  return obs
end
