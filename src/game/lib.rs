//! Balatro game layer — the fast, headless simulator (ARCHITECTURE.md §3.1).
//!
//! Module map (single source of truth = `rules`):
//!   rules  -> authoritative game state, cards, jokers, consumables, bosses, scoring
//!   sim    -> transition function + stage machine; sole enforcer of legality
//!   solver -> tactical optimiser (Layer 1); pure & stateless
//!   env    -> RL boundary: reset/step/mask + reward + observation encoder (pyo3)

pub mod rules;
pub mod sim;
pub mod solver;
pub mod env;
