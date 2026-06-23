//! Scoring pipeline & order of operations (makes joker order matter):
//! base hand -> per-card scoring -> enhancement/seal/edition effects -> joker hooks
//! -> final `chips x mult`. Big-number arithmetic for late-game scores. (ARCHITECTURE.md §3.1)
