import math
import numpy as np
from scipy.ndimage import gaussian_filter
from config import WIDTH, HEIGHT, NUM_ODOR_TYPES, PATCH_WIDTH, PATCH_HEIGHT, SCALE, PATCHES, SENSOR_DISTANCE

def update_odors():
    """Applies diffusion to odor patches and decays odor intensity over time."""
    for i in range(NUM_ODOR_TYPES):
        PATCHES[i] = gaussian_filter(PATCHES[i], sigma=1) * 0.95

def convert_patch_to_coord(x, y):
    """Converts screen coordinates to odor patch grid coordinates."""
    px = int((x - WIDTH / 2) * SCALE + PATCH_WIDTH / 2)
    py = int((y - HEIGHT / 2) * SCALE + PATCH_HEIGHT / 2)
    px = max(0, min(PATCH_WIDTH - 1, px))
    py = max(0, min(PATCH_HEIGHT - 1, py))
    return px, py

def sensors(x, y, heading):
    """Gets sensory input from odor patches based on the slug's heading."""
    px, py = convert_patch_to_coord(x, y)
    left_x = int(px + SENSOR_DISTANCE * math.cos(math.radians(heading + 45)))
    left_y = int(py + SENSOR_DISTANCE * math.sin(math.radians(heading + 45)))
    right_x = int(px + SENSOR_DISTANCE * math.cos(math.radians(heading - 45)))
    right_y = int(py + SENSOR_DISTANCE * math.sin(math.radians(heading - 45)))
    left_x, left_y = max(0, min(PATCH_WIDTH - 1, left_x)), max(0, min(PATCH_HEIGHT - 1, left_y))
    right_x, right_y = max(0, min(PATCH_WIDTH - 1, right_x)), max(0, min(PATCH_HEIGHT - 1, right_y))
    return PATCHES[:, left_x, left_y], PATCHES[:, right_x, right_y]

def set_patch(x, y, odorlist):
    """Deposits odor at a given location in the environment."""
    px, py = convert_patch_to_coord(x, y)
    PATCHES[:, px, py] = odorlist

def wrap_around(x, y, path=None):
    """Handles screen wrap-around and optionally tracks path breaks."""
    wrapped_x = x % WIDTH
    wrapped_y = y % HEIGHT
    if path is not None and (abs(wrapped_x - x) > WIDTH / 2 or abs(wrapped_y - y) > HEIGHT / 2):
        path.append(None)
    return wrapped_x, wrapped_y