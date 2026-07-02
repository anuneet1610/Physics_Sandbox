# ------------------------
# Shared mutable simulation state
# ------------------------

g  = 9.81
e  = 1.0
mu = 1.0
G  = 1

dt = 0.0  # updated once per frame in full_code.py

mode = "BALL"

# interaction state used across event handling + ui
wall_drawing        = False
wall_start_wx       = 0.0
wall_start_wy       = 0.0
spring_selected_obj = None
selected_obj        = None  # ball/rectangle currently shown in the bottom info panel
editing_field       = None  # field key currently being edited e.g. "mass", "vx", "x" …
editing_text        = ""    # text buffer for the active edit
paused = False

WORLD_WIDTH = 50
WORLD_HEIGHT = 30

left_wall = 0
right_wall = WORLD_WIDTH
ground = 0
ceiling = WORLD_HEIGHT

sim_time = 0.0

# rolling kinematics history for the graphs: list of (t, x, y, vx, vy)
GRAPH_HISTORY_SECONDS = 5.0
position_history = []  # cleared/rebuilt when selection changes
