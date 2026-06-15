# Balatro ML task runner — run `just` to list recipes.
# All Python runs through `uv run` so the project .venv is used automatically.

# Show available recipes
default:
    @just --list

# Run an arbitrary Python script with args, e.g. `just run scripts/verify_bridge.py`
run script *args:
    uv run python {{script}} {{args}}

# Train the agent
train *args:
    uv run python scripts/train.py {{args}}

# Launch the Streamlit dashboard
dashboard *args:
    uv run streamlit run scripts/dashboard.py {{args}}

# Verify the Balatro <-> Python bridge
verify-bridge *args:
    uv run python scripts/verify_bridge.py {{args}}

# Record a human gameplay session
record *args:
    uv run python scripts/record_human.py {{args}}

# Hot-reload the Balatro mod
reload-mod *args:
    uv run python scripts/reload_mod.py {{args}}

# Seed the dashboard with sample games
seed-dashboard *args:
    uv run python scripts/seed_dashboard.py {{args}}

# Run the test suite
test *args:
    uv run pytest {{args}}
