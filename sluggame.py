import pygame 
import math
import random
import numpy as np
from scipy.ndimage import gaussian_filter

# Initialize Pygame
pygame.init()

# Set up the screen
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cyberslug Simulation")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (165, 42, 42)
CYAN = (0, 255, 255)
PINK = (255, 105, 180)
YELLOW = (255, 255, 0)

# Set up clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60  # Run simulation at 60 frames per second

# Number of odors
num_odor_types = 4

# --- Odor Patch Environment Setup ---
pwidth, pheight = 200, 200
# Each odor type gets its own layer in the patches array
patches = np.zeros((num_odor_types, pwidth, pheight))
# Define a scaling factor to convert screen coordinates to patch coordinates
scale = pwidth / WIDTH # Assumes WIDTH == HEIGHT

def UpdateOdors():
    global patches
    for i in range(num_odor_types):
        patches[i] = gaussian_filter(patches[i], sigma=1)
        patches[i] *= 0.95

def ConvertPatchToCoord(x, y, patches):
    # Convert screen coords (0 to WIDTH) to patch coords (centered)
    # First center the coordinates around the middle of the screen
    x_centered = x - WIDTH / 2
    y_centered = y - HEIGHT / 2
    # Scale from screen to patch size and recenter patch coordinates
    px = int(x_centered * scale + pwidth / 2)
    py = int(y_centered * scale + pheight / 2)
    # Clamp to valid patch indices
    px = max(0, min(pwidth - 1, px))
    py = max(0, min(pheight - 1, py))
    return px, py

def Sensors(x, y, heading, patches):
    sdist = 4 # distance (in patch units) from the cnter to sensor sample point
    px, py = ConvertPatchToCoord(x, y, patches)
    # Calculate left and right sensor positions relative to the heading
    left_x = int(px + sdist * math.cos(math.radians(heading + 45)))
    left_y = int(py + sdist * math.sin(math.radians(heading + 45)))
    right_x = int(px + sdist * math.cos(math.radians(heading - 45)))
    right_y = int(py + sdist * math.sin(math.radians(heading - 45)))
    # Clamp sensor coords within patch boundaries
    left_x = max(0, min(pwidth - 1, left_x))
    left_y = max(0, min(pheight - 1, left_y))
    right_x = max(0, min(pwidth - 1, right_x))
    right_y = max(0, min(pheight - 1, right_y))
    # Get the sensor values from the patches
    sensors_left = patches[:, left_x, left_y]
    sensors_right = patches[:, right_x, right_y]
    return sensors_left, sensors_right

def SetPatch(x, y, odorlist, patches):
    px, py = ConvertPatchToCoord(x, y, patches)
    patches[:, px, py] = odorlist

# Prey odor definitions
flab_odorlist = [0.5, 0, 0.5, 0]
hermi_odorlist = [0.5, 0.5, 0, 0]
drug_odorlist = [0, 0, 0, 0.5]


# --- Pygame Simulation Classes ---

class Cyberslug:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 0 # degrees
        self.speed = 3
        self.path = [(self.x, self.y)]  # Start with the initial position
        self.last_x = self.x
        self.last_y = self.y

        # ASIMOV dynamics variables
        self.nutrition = 0.5
        self.incentive = 0.0
        self.satiation = 0.0

        # Learning variables for prey types
        self.Vh = 0.0
        self.Vf = 0.0
        self.Vd = 0.0

        # Learning parameters
        self.alpha_hermi = 0.5;  self.beta_hermi = 1.0;  self.lambda_hermi = 1.0
        self.alpha_flab  = 0.5;  self.beta_flab  = 1.0;  self.lambda_flab  = 1.0
        self.alpha_drug  = 0.5;  self.beta_drug  = 1.0;  self.lambda_drug  = 1.0

        # Sensor and pain parameters
        self.sns_pain_left = 0.0
        self.sns_pain_right = 0.0
        self.spontaneous_pain = 2.0

        # Counters and timers
        self.encounter_timer = 0
        self.hermi_counter = 0
        self.flab_counter = 0
        self.drug_counter = 0
        self.rewardExperience = 0
        self.app_state_switch = 0

        # Initialize sensor arrays 
        self.sns_odors_left = [0.0] * num_odor_types
        self.sns_odors_right = [0.0] * num_odor_types
        self.sns_odors = [0.0] * num_odor_types

    def update(self, sensors_left, sensors_right, encounter):
        # --- Process sensor readings ---
        # Convert odor concentrations to a logarithmic scale
        self.sns_odors_left = [0 if i <= 1e-7 else (7 + math.log10(i)) for i in sensors_left]
        self.sns_odors_right = [0 if i <= 1e-7 else (7 + math.log10(i)) for i in sensors_right]
        self.sns_odors = [(l + r) / 2 for l, r in zip(self.sns_odors_left, self.sns_odors_right)]
        # Assume sensor order: 0: odor_betaine, 1: odor_hermi, 2: odor_flab, 3: odor_drug
        sns_betaine = self.sns_odors[0]
        sns_hermi = self.sns_odors[1]
        sns_flab = self.sns_odors[2]
        sns_drug = self.sns_odors[3]

        # --- Associative learning from prey encounters ---
        if encounter == "hermi":
            self.Vh += self.alpha_hermi * self.beta_hermi * (self.lambda_hermi - self.Vh)
            self.nutrition += 0.1
            if self.encounter_timer == 0:
                self.hermi_counter += 1
        if encounter == "flab":
            self.Vf += self.alpha_flab * self.beta_flab * (self.lambda_flab - self.Vf)
            self.nutrition += 0.1
            if self.encounter_timer == 0:
                self.flab_counter += 1
        if encounter == "drug":
            self.Vd += self.alpha_drug * self.beta_drug * (self.lambda_drug - self.Vd)
            if self.encounter_timer == 0:
                self.drug_counter += 1
        
        # --- Pain Calcuations ---
        self.sns_pain = (self.sns_pain_left + self.sns_pain_right)/2
        self.pain = 10 / (1 + math.exp(-2 * (self.sns_pain + self.spontaneous_pain) + 10 ))
        self.pain_switch = 1 - 2 / (1 + math.exp(-10 * (self.sns_pain - 0.2)));
    
        # --- Nutrition, Satiation, and Incentive Calculations ---
        self.nutrition -= 0.005 * self.nutrition
        self.satiation = 1 / ((1 + 0.7 * math.exp(-4 * self.nutrition + 2)) ** 2)
        self.reward_pos = (sns_betaine / (1 + (0.05 * self.Vh * sns_hermi) - 0.006 / self.satiation) + 
                           3.0 * self.Vh * sns_hermi + 8.0 * self.Vd * sns_drug)
        self.reward_neg = 0.59 * self.Vf * sns_flab
        self.incentive = self.reward_pos - self.reward_neg

        # --- Somatic Map Calculation ---
        # Combine sensor inputs from odors (ignoring first) with the pain sensor
        self.somatic_map_senses_left = self.sns_odors_left[1:] + [self.sns_pain_left]
        self.somatic_map_senses_right = self.sns_odors_right[1:] + [self.sns_pain_right]
        # Compute the average for each sensor pair
        self.somatic_map_senses = [(l + r) / 2 for l, r in 
                                   zip(self.somatic_map_senses_left, self.somatic_map_senses_right)]
        # Calculate somatic factors: each sensor's value relative to the total
        self.somatic_map_factors = [2 * sensor - sum(self.somatic_map_senses) for sensor in self.somatic_map_senses]
        # Replace the last factor with the computed pain value to emphasize pain's influence 
        self.somatic_map_factors[-1] = self.pain
        # Apply a sigmoid to the difference between left and right sensor values modulated by the factor
        self.somatic_map_sigmoids = [
            (l - r) / (1 + math.exp(-50 * factor))
            for l, r, factor in zip(self.somatic_map_senses_left, self.somatic_map_senses_right, self.somatic_map_factors)
        ]
        # The somatic map is the negative sum of the sigmoid values
        self.somatic_map = -sum(self.somatic_map_sigmoids)

        # --- Appetitive State and Turn Angle ---
        self.app_state = 0.01 + (
            1 / (1 + math.exp(- (1 * self.incentive - 8 * self.satiation - 0.1 * self.pain - 0.1 * self.pain_switch * self.rewardExperience))) + 
            0.1 * ((self.app_state_switch - 1) * 0.5)
        )
        self.app_state_switch = (-2 / (1 + math.exp(-100 * (self.app_state - 0.245)))) + 1
        self.turn_angle = 3 * ((2 * self.app_state_switch) / (1 + math.exp(3 * self.somatic_map)) - self.app_state_switch)

        # --- Encounter Timer ---
        if self.encounter_timer > 0:
            self.encounter_timer -= 1
        if encounter != "none" and self.encounter_timer == 0:
            print("Tick encountered", encounter, 
                  "Flab:", self.flab_counter, 
                  "Hermi:", self.hermi_counter, 
                  "Drug:", self.drug_counter)
            print("Satiation:", round(self.satiation, 4),
                  "Nutrition:", round(self.nutrition, 2),
                  "Incentive:", round(self.incentive, 2),
                  "AppState:", round(self.app_state, 3),
                  "AppStateSwitch:", round(self.app_state_switch, 3),
                  "Somatic_Map:", round(self.somatic_map, 3),
                  "Sns_Bet:", round(sns_betaine, 2),
                  "Sns_Hermi:", round(sns_hermi, 2),
                  "Sns_Flab:", round(sns_flab, 2),
                  "Sns_Drug:", round(sns_drug, 2),
                  "Vh:", round(self.Vh, 2),
                  "Vf:", round(self.Vf, 2),
                  "Vd:", round(self.Vd, 2))
            self.encounter_timer = 10
        
        return self.turn_angle

    def draw(self):
        """Draw the slug and its path trace without crossing lines."""
        # Draw the path in segments, breaking on None
        if len(self.path) > 1:
            # We'll accumulate segments in a list
            segment = []
            for point in self.path:
                if point is None:
                    # Draw the segment collected so far
                    if len(segment) > 1:
                        pygame.draw.lines(screen, BLACK, False, segment, 2)
                    segment = []
                else:
                    segment.append(point)
            # Draw any leftover segment
            if len(segment) > 1:
                pygame.draw.lines(screen, BLACK, False, segment, 2)

        # Draw the slug
        tip = (self.x + 25 * math.cos(math.radians(self.angle)),
               self.y + 25 * math.sin(math.radians(self.angle)))
        left = (self.x - 10 * math.cos(math.radians(self.angle + 140)),
                self.y - 10 * math.sin(math.radians(self.angle + 140)))
        right = (self.x - 10 * math.cos(math.radians(self.angle - 140)),
                 self.y - 10 * math.sin(math.radians(self.angle - 140)))
        pygame.draw.polygon(screen, BROWN, [tip, left, right])


class Prey:
    def __init__(self, x, y, color, odorlist):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 5  # Small circle for prey
        self.angle = random.uniform(0, 360)
        self.odorlist = odorlist

    def move(self):
        """Update prey position with a simple random turn and a fixed forward step."""
        # Turn a small random amount: NetLogo does rt -1 + random-float 2
        self.angle += random.uniform(-1, 1)
        # Move forward a small fixed step (adjust step size as needed)
        step = 0.1
        self.x += step * math.cos(math.radians(self.angle))
        self.y += step * math.sin(math.radians(self.angle))
        # Wrap-around: if the prey goes off one side, appear on the opposite side
        if self.x > WIDTH:
            self.x = 0
        elif self.x < 0:
            self.x = WIDTH
        if self.y > HEIGHT:
            self.y = 0
        elif self.y < 0:
            self.y = HEIGHT

    def respawn(self):
        """Respawn prey at a random location."""
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.angle = random.uniform(0, 360)

    def draw(self):
        """Draw prey on the screen."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)


# --- Main Simulation Loop ---
# Initialize the slug and prey
cslug = Cyberslug()
prey_list = []
# Create prey of three types
for _ in range(4):
    prey_list.append(Prey(random.randint(0, WIDTH), random.randint(0, HEIGHT), CYAN, hermi_odorlist))
for _ in range(4):
    prey_list.append(Prey(random.randint(0, WIDTH), random.randint(0, HEIGHT), PINK, flab_odorlist))
for _ in range(4):
    prey_list.append(Prey(random.randint(0, WIDTH), random.randint(0, HEIGHT), YELLOW, drug_odorlist))

running = True
tick = 0
total_ticks = 1000000

while tick < total_ticks and running:
    screen.fill(WHITE)
    tick += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update patches: first each prey deposits odor onto the patch
    for prey in prey_list:
        SetPatch(prey.x, prey.y, prey.odorlist, patches)
    # Diffuse and decay odors
    UpdateOdors()

    # Move and draw prey
    for prey in prey_list:
        prey.move()
        prey.draw()

    # Slug movement logic
    encounter = "none"
    for prey in prey_list:
        if math.hypot(prey.x - cslug.x, prey.y - cslug.y) < 10:  # Collision detection
            if prey.color == CYAN:
                encounter = "hermi"
            elif prey.color == PINK:
                encounter = "flab"
            elif prey.color == YELLOW:
                encounter = "drug"
            prey.respawn()

    # Simulate slug sensors (simplified)
    sensors_left, sensors_right = Sensors(cslug.x, cslug.y, cslug.angle, patches)
    # print("Sensors Left:", sensors_left, "Sensors Right:", sensors_right)  # <-- DEBUG
    # Update the slug and capture the computed turn angle
    turn_angle = cslug.update(sensors_left, sensors_right, encounter)
    # Update heading based on the turn angle
    cslug.angle -= turn_angle

    # --- Path-Breaking Logic ---
    prev_x, prev_y = cslug.x, cslug.y
    new_x = (cslug.x + cslug.speed * math.cos(math.radians(cslug.angle))) % WIDTH
    new_y = (cslug.y + cslug.speed * math.sin(math.radians(cslug.angle))) % HEIGHT
    # If the distance between the new position and the previous one is large,
    # it means we wrapped around, so insert a break in the path.
    if abs(new_x - prev_x) > WIDTH/2 or abs(new_y - prev_y) > HEIGHT/2:
        cslug.path.append(None)
    cslug.x, cslug.y = new_x, new_y
    cslug.path.append((cslug.x, cslug.y))

    cslug.draw()
    pygame.display.flip()  # Update display
    clock.tick(FPS)  # Limit frame rate to 60 FPS

pygame.quit()
