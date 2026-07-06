import config
import state

box_width  = config.BOX_RIGHT - config.BOX_LEFT
box_height = config.BOX_BOTTOM - config.BOX_TOP
pixels_per_meter_x = box_width  / state.WORLD_WIDTH
pixels_per_meter_y = box_height / state.WORLD_HEIGHT

# ------------------------
# Coordinate helpers
# ------------------------

def world_to_screen(wx, wy):
    sx = config.BOX_LEFT + wx * pixels_per_meter_x
    sy = config.BOX_BOTTOM - wy * pixels_per_meter_y
    return int(sx), int(sy)

def screen_to_world(sx, sy):
    wx = (sx - config.BOX_LEFT)   / pixels_per_meter_x
    wy = (config.BOX_BOTTOM - sy) / pixels_per_meter_y
    return wx, wy