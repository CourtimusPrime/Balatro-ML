"""Training orchestrator: drives rollouts against the vectorised `env`, computes
advantages, runs PPO updates, and controls the curriculum (ante_end, joker subset,
run length) that escalates difficulty as the agent improves. (ARCHITECTURE.md §3.2.2)
"""
