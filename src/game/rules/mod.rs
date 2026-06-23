//! Authoritative game rules & state — the single source of truth (ARCHITECTURE.md §3.1).

pub mod state; // GameState: deck, hand, held jokers, consumables, money, ante/blind, hand levels
pub mod card; // Card type: rank, suit + Enhancement / Seal / Edition enums (data)
pub mod jokers; // 150 joker definitions + effect impls + shop generation
pub mod consumables; // Tarot / Planet / Spectral: catalog + use-effects + shop generation
pub mod bosses; // Boss-blind modifiers (ported from calculator/ fork)
pub mod calc; // Scoring pipeline & order of operations; invokes joker/card-effect hooks
