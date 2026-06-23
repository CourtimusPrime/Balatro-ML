//! RL boundary: reset / step / legal-mask, the reward function, and the observation
//! encoder (state -> feature vector with card & joker identity + solver eval).
//! Vectorised (batched step) and exposed to Python via pyo3. (ARCHITECTURE.md §3.1, §9.1)
