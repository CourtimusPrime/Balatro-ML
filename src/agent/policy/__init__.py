"""Policy / value networks: observation -> action distribution + value estimate.

Uses MaskablePPO (SB3-contrib) or a CleanRL masked-PPO variant; the legal-action mask
from `env` is applied before sampling so illegal actions are never chosen. (ARCHITECTURE.md §3.2.1)
"""
