"""Run store: persists run telemetry, training curves, and offline datasets (BC data,
expert/solver trajectories). NOT what PPO learns from — on-policy PPO updates from the
current rollout batch and discards it. For telemetry, eval, BC bootstrap, reproducibility.
(ARCHITECTURE.md §3.2.4)
"""
