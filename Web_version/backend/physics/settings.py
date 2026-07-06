"""Shared tunable constants (mirrors the old state.py globals, but scoped
inside a SimulationState instance rather than module-level globals so that
multiple simulations / test runs don't clobber each other)."""

WORLD_WIDTH = 50
WORLD_HEIGHT = 30

GRAPH_HISTORY_SECONDS = 5.0
NUM_BOUNDARY_WALLS = 4
REST_THRESHOLD = 0.3

# Physics runs on a fixed timestep rather than raw wall-clock deltas, so
# jitter from asyncio/network scheduling can't inflate dt and cause fast
# objects to tunnel through walls. If an object is moving fast enough that
# even this fixed dt would let it skip past thin geometry in one go, the
# frame is split into multiple smaller sub-steps (see simulation.py).
FIXED_DT = 1 / 60
MAX_SUBSTEPS = 8
SUBSTEP_DISTANCE = 0.25  # world units of travel allowed per sub-step
