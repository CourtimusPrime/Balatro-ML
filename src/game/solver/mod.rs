//! Tactical optimiser (Layer 1). Given a hand, jokers, remaining hands/discards, target,
//! and boss effect, searches play/discard subsets (scored via `calc`) and returns the best.
//! Greedy initially; expectimax-over-draw later. Pure and stateless. (ARCHITECTURE.md §3.1)
