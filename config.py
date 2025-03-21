import numpy as np

# Debug toggle
DEBUG_MODE = False

# Simulation settings
WIDTH, HEIGHT = 600, 600
FPS = 60
PREY_DISTANCE = 4
EDGE_DISTANCE = 4
SENSOR_DISTANCE = 4
PREY_RADIUS = 4

# Encounter handling
ENCOUNTER_COOLDOWN = 10

# Odor patch grid
NUM_ODOR_TYPES = 4
PATCH_WIDTH, PATCH_HEIGHT = 200, 200
SCALE = PATCH_WIDTH / WIDTH # Assumes WIDTH == HEIGHT
PATCHES = np.zeros((NUM_ODOR_TYPES, PATCH_WIDTH, PATCH_HEIGHT))

# Default populations
HERMI_POPULATION_DEFAULT = 4
FLAB_POPULATION_DEFAULT = 4
FAUXFLAB_POPULATION_DEFAULT = 4

# Learning rates
ALPHA_HERMI = 0.5
BETA_HERMI = 1.0
LAMBDA_HERMI = 1.0

ALPHA_FLAB = 0.5
BETA_FLAB = 1.0
LAMBDA_FLAB = 1.0

ALPHA_DRUG = 0.5
BETA_DRUG = 1.0
LAMBDA_DRUG = 1.0

# Prey Odors
FLAB_ODOR = [0.5, 0, 0.5, 0]
HERMI_ODOR = [0.5, 0.5, 0, 0]
DRUG_ODOR = [0, 0, 0, 0.5]

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (165, 42, 42)
CYAN = (0, 255, 255)
PINK = (255, 105, 180)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

# Simulation settings
TOTAL_TICKS = 1_000_000

# UI settings
UI_UPDATE_INTERVAL = 100