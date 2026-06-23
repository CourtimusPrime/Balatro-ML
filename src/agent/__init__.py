"""Balatro RL learner — the Python layer (ARCHITECTURE.md §3.2).

Packages:
    policy  -- neural policy/value networks (MaskablePPO / masked CleanRL PPO)
    train   -- rollout orchestration, curriculum control, hyperparameters
    store   -- run telemetry, eval datasets, BC/offline data (NOT the PPO learning substrate)
    eval    -- held-out-seed win rates; scorer-vs-calculator oracle checks
"""
