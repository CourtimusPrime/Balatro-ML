"""
Tests for src.env.reward.compute_reward (ENV-02).

All tests run fully offline — no live game or socket required. Unit tests cover
numeric contracts: finite output, illegal-action penalty, negative-margin clamping,
terminal final_score bonus, edge-case float stability, and formula correctness.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.env.reward import compute_reward


# ---------------------------------------------------------------------------
# ENV-02 — reward function unit tests
# ---------------------------------------------------------------------------


def test_reward_zero_chips_finite() -> None:
    """compute_reward with all-zero inputs returns a finite float."""
    result = compute_reward(
        chips_scored=0,
        margin_over_blind=0,
        hand_type_level_gain=0.0,
        deck_size_reduction=0.0,
    )
    assert isinstance(result, float)
    assert math.isfinite(result)


def test_reward_illegal_action() -> None:
    """compute_reward with illegal=True returns exactly -1.0."""
    result = compute_reward(
        chips_scored=100,
        margin_over_blind=50,
        hand_type_level_gain=1.0,
        deck_size_reduction=2.0,
        illegal=True,
    )
    assert result == -1.0


def test_reward_negative_margin_clamped() -> None:
    """Negative margin_over_blind is clamped to 0 — result is finite and >= 0."""
    result = compute_reward(
        chips_scored=100,
        margin_over_blind=-50,
        hand_type_level_gain=0.0,
        deck_size_reduction=0.0,
    )
    assert math.isfinite(result)
    assert result >= 0.0


def test_reward_final_score_terminal() -> None:
    """Terminal step with final_score produces higher reward than non-terminal."""
    base = compute_reward(
        chips_scored=100,
        margin_over_blind=50,
        hand_type_level_gain=0.0,
        deck_size_reduction=0.0,
    )
    terminal = compute_reward(
        chips_scored=100,
        margin_over_blind=50,
        hand_type_level_gain=0.0,
        deck_size_reduction=0.0,
        final_score=1_000_000,
    )
    assert terminal > base


def test_reward_finite_edges() -> None:
    """Very large inputs remain finite (no NaN or inf)."""
    result = compute_reward(
        chips_scored=10**9,
        margin_over_blind=10**9,
        hand_type_level_gain=10.0,
        deck_size_reduction=10.0,
        final_score=10**12,
    )
    assert np.isfinite(result)


def test_reward_formula_values() -> None:
    """compute_reward matches the README formula to within 1e-9."""
    result = compute_reward(
        chips_scored=99,
        margin_over_blind=49,
        hand_type_level_gain=1.0,
        deck_size_reduction=2.0,
    )
    expected = (
        math.log(100)
        + 2.0 * math.log(50)
        + 0.5 * 1.0
        + 0.1 * 2.0
    )
    assert abs(result - expected) < 1e-9
