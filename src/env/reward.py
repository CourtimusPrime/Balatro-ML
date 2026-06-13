"""
Reward computation for BalatroEnv.

Numeric contracts:
  - Returns a finite float for every valid input combination.
  - Illegal-action penalty is exactly -1.0; no other computation is performed.
  - margin_over_blind is clamped to >= 0 before the log, so a lost blind
    yields a 0 contribution rather than NaN/-inf.
  - Final guard: np.nan_to_num ensures no NaN or ±inf escapes this module.
  - Terminal bonus adds 5 * log(final_score + 1) only when final_score is given.

Formula (README §Reward Function, authoritative):
  reward = log(chips_scored + 1)
         + 2.0 * log(max(0, margin_over_blind) + 1)
         + 0.5 * hand_type_level_gain
         + 0.1 * deck_size_reduction
         + 5.0 * log(final_score + 1)   [only if final_score is not None]
"""

from __future__ import annotations

import math

import numpy as np
from loguru import logger


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_reward(
    chips_scored: int,
    margin_over_blind: int,
    hand_type_level_gain: float,
    deck_size_reduction: float,
    final_score: int | None = None,
    illegal: bool = False,
) -> float:
    """Return the scalar reward for one environment step.

    Parameters
    ----------
    chips_scored:
        Chips scored during this hand (>= 0).
    margin_over_blind:
        chips_scored - chips_needed; may be negative (lost blind) — clamped to 0.
    hand_type_level_gain:
        How many levels the played hand type has gained this run.
    deck_size_reduction:
        How many cards have been permanently removed from the deck.
    final_score:
        Cumulative run score at terminal step; None for non-terminal steps.
    illegal:
        If True the action was illegal; returns the penalty immediately.
    """
    if illegal:
        logger.warning("Illegal action penalty applied")
        return -1.0

    margin = max(0, margin_over_blind)
    r = (
        math.log(chips_scored + 1)
        + 2.0 * math.log(margin + 1)
        + 0.5 * hand_type_level_gain
        + 0.1 * deck_size_reduction
        + (5.0 * math.log(final_score + 1) if final_score is not None else 0.0)
    )
    return float(np.nan_to_num(r, nan=0.0, posinf=1e6, neginf=-1e6))
