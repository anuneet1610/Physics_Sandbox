# ------------------------
# Shared mutable simulation state
# ------------------------

g  = 0
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
controlled_ball     = None
selected_obj        = None  # ball/rectangle currently shown in the bottom info panel
editing_field       = None  # field key currently being edited, e.g. "mass", "vx", "x" …
editing_text        = ""    # text buffer for the active edit

CONTROL_SPEED = 10.0

WORLD_WIDTH = 50
WORLD_HEIGHT = 30

left_wall = 0
right_wall = WORLD_WIDTH
ground = 0
ceiling = WORLD_HEIGHT