"""
String→int lookup tables for Balatro game entities.

Each map converts a raw string key emitted by mod/state.lua on the wire to a
stable integer index used in the observation tensors.  Maps are static and
hard-coded (vanilla base-game only; unknown/modded keys return -1).

Sentinel contract
-----------------
- Unknown key   → -1  (default absent_sentinel; use for all error-path detection)
- Absent/optional field (no edition, no seal, stone card suit/value)
  → 0  (callers pass absent_sentinel=0 for optional fields)
- Already-int value  → returned as-is  (_get pass-through)

Maps exported
-------------
SUIT_MAP, VALUE_MAP, ENHANCEMENT_MAP, EDITION_MAP, SEAL_MAP,
JOKER_ID_MAP, TAROT_ID_MAP, PLANET_ID_MAP, SPECTRAL_ID_MAP,
CONSUMABLE_TYPE_MAP, PACK_TYPE_MAP, VOUCHER_ID_MAP, BOSS_BLIND_ID_MAP
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get(table: dict[str, int], key: object, absent_sentinel: int = -1) -> int:
    """Look up *key* in *table*; return *absent_sentinel* when missing.

    - If *key* is already an ``int``, return it unchanged (pass-through).
    - Otherwise coerce to ``str`` and do a dict lookup.
    - Unknown keys default to -1; callers use absent_sentinel=0 for optional
      absent fields (edition, seal, suit/value of stone cards).
    """
    if isinstance(key, int):
        return key
    return table.get(str(key), absent_sentinel)


# ---------------------------------------------------------------------------
# Card attribute maps
# ---------------------------------------------------------------------------

SUIT_MAP: dict[str, int] = {
    "Spades":   1,
    "Clubs":    2,
    "Hearts":   3,
    "Diamonds": 4,
}
# Absent / stone → 0  (caller supplies absent_sentinel=0)

VALUE_MAP: dict[str, int] = {
    "2":  2, "3":  3, "4":  4, "5":  5, "6":  6,
    "7":  7, "8":  8, "9":  9, "10": 10,
    "Jack": 11, "Queen": 12, "King": 13, "Ace": 14,
}
# Absent / stone → 0  (caller supplies absent_sentinel=0)

ENHANCEMENT_MAP: dict[str, int] = {
    "Base":       0,
    "Bonus Card": 1,
    "Mult Card":  2,
    "Wild Card":  3,
    "Glass Card": 4,
    "Steel Card": 5,
    "Stone Card": 6,
    "Gold Card":  7,
    "Lucky Card": 8,
}

EDITION_MAP: dict[str, int] = {
    "foil":       1,
    "holo":       2,
    "polychrome": 3,
    "negative":   4,   # jokers only
}
# Absent / no edition → 0  (caller supplies absent_sentinel=0)

SEAL_MAP: dict[str, int] = {
    "Gold":   1,
    "Red":    2,
    "Blue":   3,
    "Purple": 4,
}
# Absent / no seal → 0  (caller supplies absent_sentinel=0)

# ---------------------------------------------------------------------------
# Joker ID map — 150 jokers in internal collection order
# Source: github.com/BurndiL/BalatroAP ap_connection.lua (j_whitelist)
# ---------------------------------------------------------------------------

JOKER_ID_MAP: dict[str, int] = {
    "j_joker": 0,
    "j_greedy_joker": 1,
    "j_lusty_joker": 2,
    "j_wrathful_joker": 3,
    "j_gluttenous_joker": 4,
    "j_jolly": 5,
    "j_zany": 6,
    "j_mad": 7,
    "j_crazy": 8,
    "j_droll": 9,
    "j_sly": 10,
    "j_wily": 11,
    "j_clever": 12,
    "j_devious": 13,
    "j_crafty": 14,
    "j_half": 15,
    "j_stencil": 16,
    "j_four_fingers": 17,
    "j_mime": 18,
    "j_credit_card": 19,
    "j_ceremonial": 20,
    "j_banner": 21,
    "j_mystic_summit": 22,
    "j_marble": 23,
    "j_loyalty_card": 24,
    "j_8_ball": 25,
    "j_misprint": 26,
    "j_dusk": 27,
    "j_raised_fist": 28,
    "j_chaos": 29,
    "j_fibonacci": 30,
    "j_steel_joker": 31,
    "j_scary_face": 32,
    "j_abstract": 33,
    "j_delayed_grat": 34,
    "j_hack": 35,
    "j_pareidolia": 36,
    "j_gros_michel": 37,
    "j_even_steven": 38,
    "j_odd_todd": 39,
    "j_scholar": 40,
    "j_business": 41,
    "j_supernova": 42,
    "j_ride_the_bus": 43,
    "j_space": 44,
    "j_egg": 45,
    "j_burglar": 46,
    "j_blackboard": 47,
    "j_runner": 48,
    "j_ice_cream": 49,
    "j_dna": 50,
    "j_splash": 51,
    "j_blue_joker": 52,
    "j_sixth_sense": 53,
    "j_constellation": 54,
    "j_hiker": 55,
    "j_faceless": 56,
    "j_green_joker": 57,
    "j_superposition": 58,
    "j_todo_list": 59,
    "j_cavendish": 60,
    "j_card_sharp": 61,
    "j_red_card": 62,
    "j_madness": 63,
    "j_square": 64,
    "j_seance": 65,
    "j_riff_raff": 66,
    "j_vampire": 67,
    "j_shortcut": 68,
    "j_hologram": 69,
    "j_vagabond": 70,
    "j_baron": 71,
    "j_cloud_9": 72,
    "j_rocket": 73,
    "j_obelisk": 74,
    "j_midas_mask": 75,
    "j_luchador": 76,
    "j_photograph": 77,
    "j_gift": 78,
    "j_turtle_bean": 79,
    "j_erosion": 80,
    "j_reserved_parking": 81,
    "j_mail": 82,
    "j_to_the_moon": 83,
    "j_hallucination": 84,
    "j_fortune_teller": 85,
    "j_juggler": 86,
    "j_drunkard": 87,
    "j_stone": 88,
    "j_golden": 89,
    "j_lucky_cat": 90,
    "j_baseball": 91,
    "j_bull": 92,
    "j_diet_cola": 93,
    "j_trading": 94,
    "j_flash": 95,
    "j_popcorn": 96,
    "j_trousers": 97,
    "j_ancient": 98,
    "j_ramen": 99,
    "j_walkie_talkie": 100,
    "j_selzer": 101,
    "j_castle": 102,
    "j_smiley": 103,
    "j_campfire": 104,
    "j_ticket": 105,
    "j_mr_bones": 106,
    "j_acrobat": 107,
    "j_sock_and_buskin": 108,
    "j_swashbuckler": 109,
    "j_troubadour": 110,
    "j_certificate": 111,
    "j_smeared": 112,
    "j_throwback": 113,
    "j_hanging_chad": 114,
    "j_rough_gem": 115,
    "j_bloodstone": 116,
    "j_arrowhead": 117,
    "j_onyx_agate": 118,
    "j_glass": 119,
    "j_ring_master": 120,
    "j_flower_pot": 121,
    "j_blueprint": 122,
    "j_wee": 123,
    "j_merry_andy": 124,
    "j_oops": 125,
    "j_idol": 126,
    "j_seeing_double": 127,
    "j_matador": 128,
    "j_hit_the_road": 129,
    "j_duo": 130,
    "j_trio": 131,
    "j_family": 132,
    "j_order": 133,
    "j_tribe": 134,
    "j_stuntman": 135,
    "j_invisible": 136,
    "j_brainstorm": 137,
    "j_satellite": 138,
    "j_shoot_the_moon": 139,
    "j_drivers_license": 140,
    "j_cartomancer": 141,
    "j_astronomer": 142,
    "j_burnt": 143,
    "j_bootstraps": 144,
    "j_caino": 145,
    "j_triboulet": 146,
    "j_yorick": 147,
    "j_chicot": 148,
    "j_perkeo": 149,
}

# ---------------------------------------------------------------------------
# Tarot ID map — 22 tarots, 0-indexed
# Source: github.com/BurndiL/BalatroAP ap_connection.lua offsets 213-234
# ---------------------------------------------------------------------------

TAROT_ID_MAP: dict[str, int] = {
    "c_fool":              0,
    "c_magician":          1,
    "c_high_priestess":    2,
    "c_empress":           3,
    "c_emperor":           4,
    "c_heirophant":        5,
    "c_lovers":            6,
    "c_chariot":           7,
    "c_justice":           8,
    "c_hermit":            9,
    "c_wheel_of_fortune": 10,
    "c_strength":         11,
    "c_hanged_man":       12,
    "c_death":            13,
    "c_temperance":       14,
    "c_devil":            15,
    "c_tower":            16,
    "c_star":             17,
    "c_moon":             18,
    "c_sun":              19,
    "c_judgement":        20,
    "c_world":            21,
}

# ---------------------------------------------------------------------------
# Planet ID map — 12 planets, 0-indexed
# Source: github.com/BurndiL/BalatroAP ap_connection.lua offsets 236-248
# ---------------------------------------------------------------------------

PLANET_ID_MAP: dict[str, int] = {
    "c_mercury":  0,
    "c_venus":    1,
    "c_earth":    2,
    "c_mars":     3,
    "c_jupiter":  4,
    "c_saturn":   5,
    "c_uranus":   6,
    "c_neptune":  7,
    "c_pluto":    8,
    "c_planet_x": 9,
    "c_ceres":   10,
    "c_eris":    11,
}

# ---------------------------------------------------------------------------
# Spectral ID map — 18 spectrals, 0-indexed
# Source: github.com/BurndiL/BalatroAP ap_connection.lua offsets 249-266
# ---------------------------------------------------------------------------

SPECTRAL_ID_MAP: dict[str, int] = {
    "c_familiar":   0,
    "c_grim":       1,
    "c_incantation": 2,
    "c_talisman":   3,
    "c_aura":       4,
    "c_wraith":     5,
    "c_sigil":      6,
    "c_ouija":      7,
    "c_ectoplasm":  8,
    "c_immolate":   9,
    "c_ankh":      10,
    "c_deja_vu":   11,
    "c_hex":       12,
    "c_trance":    13,
    "c_medium":    14,
    "c_cryptid":   15,
    "c_soul":      16,
    "c_black_hole": 17,
}

# ---------------------------------------------------------------------------
# Consumable type map — card.ability.set value emitted by state.lua
# ---------------------------------------------------------------------------

CONSUMABLE_TYPE_MAP: dict[str, int] = {
    "Tarot":    0,
    "Planet":   1,
    "Spectral": 2,
}

# ---------------------------------------------------------------------------
# Pack type map — pack_type string emitted by state.lua (derived from G.STATE)
# ---------------------------------------------------------------------------

PACK_TYPE_MAP: dict[str, int] = {
    "Arcana":    0,
    "Celestial": 1,
    "Standard":  2,
    "Buffoon":   3,
    "Spectral":  4,
}

# ---------------------------------------------------------------------------
# Voucher ID map — 32 vouchers, 0-indexed
# Source: github.com/BurndiL/BalatroAP ap_connection.lua offsets 166-197
# ---------------------------------------------------------------------------

VOUCHER_ID_MAP: dict[str, int] = {
    "v_overstock_norm":  0,
    "v_clearance_sale":  1,
    "v_hone":            2,
    "v_reroll_surplus":  3,
    "v_crystal_ball":    4,
    "v_telescope":       5,
    "v_grabber":         6,
    "v_wasteful":        7,
    "v_tarot_merchant":  8,
    "v_planet_merchant": 9,
    "v_seed_money":     10,
    "v_blank":          11,
    "v_magic_trick":    12,
    "v_hieroglyph":     13,
    "v_directors_cut":  14,
    "v_paint_brush":    15,
    "v_overstock_plus": 16,
    "v_liquidation":    17,
    "v_glow_up":        18,
    "v_reroll_glut":    19,
    "v_omen_globe":     20,
    "v_observatory":    21,
    "v_nacho_tong":     22,
    "v_recyclomancy":   23,
    "v_tarot_tycoon":   24,
    "v_planet_tycoon":  25,
    "v_money_tree":     26,
    "v_antimatter":     27,
    "v_illusion":       28,
    "v_petroglyph":     29,
    "v_retcon":         30,
    "v_palette":        31,
}

# ---------------------------------------------------------------------------
# Boss blind ID map — 28 blinds (23 regular + 5 showdown), 0-indexed
# Source: github.com/Jaydchw/joker-forge-desktop balatro-utils.ts
# ---------------------------------------------------------------------------

BOSS_BLIND_ID_MAP: dict[str, int] = {
    "bl_hook":         0,
    "bl_ox":           1,
    "bl_house":        2,
    "bl_wall":         3,
    "bl_wheel":        4,
    "bl_arm":          5,
    "bl_club":         6,
    "bl_fish":         7,
    "bl_psychic":      8,
    "bl_goad":         9,
    "bl_water":       10,
    "bl_window":      11,
    "bl_manacle":     12,
    "bl_eye":         13,
    "bl_mouth":       14,
    "bl_plant":       15,
    "bl_serpent":     16,
    "bl_pillar":      17,
    "bl_needle":      18,
    "bl_head":        19,
    "bl_tooth":       20,
    "bl_flint":       21,
    "bl_mark":        22,
    "bl_final_acorn": 23,
    "bl_final_leaf":  24,
    "bl_final_vessel": 25,
    "bl_final_heart": 26,
    "bl_final_bell":  27,
}
