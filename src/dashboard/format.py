"""Shared number-formatting helpers for the dashboard (DASH-03).

``fmt_si`` is the single SI-abbreviation helper mandated by the UI-SPEC
(§ Number Formatting): every panel and every ``st.metric`` formats scores
through it so magnitudes (Balatro scores reach 1e9+) stay readable.

  fmt_si(41_200)        -> "41.2K"
  fmt_si(3_500_000_000) -> "3.5B"
  fmt_si(1_240_000_000_000) -> "1.2T"
  fmt_si(940)           -> "940"      (thousands-separated pass-through)
  fmt_si(None)          -> "—"
"""

from __future__ import annotations

# Ordered largest-first so the first matching tier wins.
_SI_TIERS = (
    (1_000_000_000_000, "T"),
    (1_000_000_000, "B"),
    (1_000_000, "M"),
    (1_000, "K"),
)


def fmt_si(n: float | int | None) -> str:
    """Abbreviate a number with an SI suffix (K/M/B/T).

    None -> the em-dash placeholder. Values below 1,000 pass through as a
    thousands-separated integer. Larger values are shown to one decimal place
    with the appropriate suffix, dropping a trailing ``.0``.
    """
    if n is None:
        return "—"

    try:
        value = float(n)
    except (TypeError, ValueError):
        return "—"

    negative = value < 0
    value = abs(value)

    for threshold, suffix in _SI_TIERS:
        if value >= threshold:
            scaled = value / threshold
            # One decimal, but drop a redundant ".0" (e.g. 3.0K -> 3K).
            text = f"{scaled:.1f}".rstrip("0").rstrip(".")
            out = f"{text}{suffix}"
            return f"-{out}" if negative else out

    # Below 1K: thousands-separated integer.
    out = f"{int(round(value)):,}"
    return f"-{out}" if negative else out
