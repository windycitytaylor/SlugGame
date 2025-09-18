# simulation_widget.py
from PyQt5 import QtCore, QtGui, QtWidgets
import pygame, math, random, numpy as np

from sluggame import Prey, Cyberslug

from config import (
    WIDTH, HEIGHT, FPS,
    WHITE, BLACK, BROWN, RED, CYAN, PINK, YELLOW,
    DEBUG_MODE,
    FLAB_ODOR, HERMI_ODOR, DRUG_ODOR, 
    PATCHES, 
    HERMI_POPULATION_DEFAULT,
    FLAB_POPULATION_DEFAULT,
    FAUXFLAB_POPULATION_DEFAULT,
    TOTAL_TICKS,
    PREY_RADIUS
)

from utils import set_patch, update_odors, sensors, wrap_around

# Make sure Pygame is initialized (for offscreen surfaces)
pygame.init()
pygame.display.set_mode((1, 1))

class SimulationWidget(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.cslug = Cyberslug()
        self.slug_image = pygame.image.load('ASIMOV_slug_sprite.png').convert_alpha()
        self.slug_image = pygame.transform.scale(self.slug_image, (80, 80))

        self.hermi_population = HERMI_POPULATION_DEFAULT
        self.flab_population = FLAB_POPULATION_DEFAULT
        self.fauxflab_population = FAUXFLAB_POPULATION_DEFAULT

        self.prey_list = []
        self.reset_prey_population()

        # Set up a QTimer to update the simulation at roughly FPS rate
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.running = False

        self.tick = 0
        self.total_ticks = TOTAL_TICKS
        self.show_sensors = False
    
    def reset_prey_population(self):
        """Rebuild the prey list based on slider values."""
        self.prey_list.clear()

        for _ in range(self.hermi_population):
            self.prey_list.append(
                Prey(
                    random.randint(0, WIDTH),
                    random.randint(0, HEIGHT),
                    CYAN, 
                    HERMI_ODOR
                    )
                )
        for _ in range(self.flab_population):
            self.prey_list.append(
                Prey(
                    random.randint(0, WIDTH),
                    random.randint(0, HEIGHT),
                    PINK, 
                    FLAB_ODOR
                    )
                )
        for _ in range(self.fauxflab_population):
            self.prey_list.append(
                Prey(
                    random.randint(0, WIDTH),
                    random.randint(0, HEIGHT),
                    YELLOW, 
                    DRUG_ODOR
                    )
                )
    
    def toggle_sensors(self):
        """Toggle the visibility of sensor visualization."""
        self.show_sensors = not self.show_sensors
        print(f"Sensors visualization: {'ON' if self.show_sensors else 'OFF'}")
        self.update_simulation()

    def update_simulation(self):
        """Runs one simulation step."""
        self.surface.fill(WHITE)
        self.tick += 1

        self.update_odor_patches()
        self.move_prey()
        self.move_cyberslug()

        self.update_slug_mask()
        self.process_encounters()

        self.render_simulation()
        self.clock.tick(FPS)

    def update_odor_patches(self):
        """Updates odors and deposits new scents."""
        for prey in self.prey_list:
            set_patch(prey.x, prey.y, prey.odorlist)
        update_odors()

    def move_prey(self):
        """Moves all prey in the environment."""
        for prey in self.prey_list:
            prey.move()

    def process_encounters(self):
        """Checks if Cyberslug encounters prey and updates counters."""
        encounter = "none"
        for prey in self.prey_list:
            prey_topleft = (prey.x - prey.radius, prey.y - prey.radius)
            offset_x = int(prey_topleft[0] - self.cslug.mask_topleft[0])
            offset_y = int(prey_topleft[1] - self.cslug.mask_topleft[1])

            if self.cslug.mask.overlap(self.create_circle_mask(prey.radius), (offset_x, offset_y)):
                encounter = self.get_encounter_type(prey)
                prey.respawn()
        
        sensors_left, sensors_right = sensors(self.cslug.x, self.cslug.y, self.cslug.angle)
        turn_angle = self.cslug.update(sensors_left, sensors_right, encounter)
        self.cslug.angle -= 2 * turn_angle
    
    def get_encounter_type(self, prey):
        """Determines encounter type based on prey color."""
        if prey.color == CYAN:
            return "hermi"
        elif prey.color == PINK:
            return "flab"
        elif prey.color == YELLOW:
            return "drug"
        return "none"

    def move_cyberslug(self):
        """Moves the Cyberslug and updates its path."""
        self.cslug.x, self.cslug.y = wrap_around(
            self.cslug.x + self.cslug.speed * math.cos(math.radians(self.cslug.angle)),
            self.cslug.y + self.cslug.speed * math.sin(math.radians(self.cslug.angle)),
            self.cslug.path
        )
        self.cslug.path.append((self.cslug.x, self.cslug.y))

    def render_simulation(self):
        """Handles rendering the simulation."""
        self.draw_prey(self. surface, self.prey_list)
        self.draw_cyberslug(self.surface, self.cslug)

        if self.show_sensors:
            sensors_left, sensors_right = sensors(self.cslug.x, self.cslug.y, self.cslug.angle)
            self.draw_sensors(sensors_left, sensors_right)

        # Convert Pygame surface to QImage and show
        image_str = pygame.image.tostring(self.surface, 'RGB')
        qimage = QtGui.QImage(image_str, WIDTH, HEIGHT, QtGui.QImage.Format_RGB888)
        scaled_image = qimage.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setPixmap(QtGui.QPixmap.fromImage(scaled_image))

    def draw_prey(self, surface, prey_list):
        """Draw all prey in the simulation."""
        for prey in prey_list:
            pygame.draw.circle(
                surface, 
                prey.color, 
                (int(prey.x), int(prey.y)), 
                PREY_RADIUS
            )

    def draw_cyberslug(self, surface, cyberslug):
        """Draw the Cyberslug and its path."""
        if len(cyberslug.path) > 1:
            segment = []
            for point in cyberslug.path:
                if point is None:
                    if len(segment) > 1:
                        pygame.draw.lines(surface, BLACK, False, segment, 1)
                    segment = []
                else:
                    segment.append(point)
            if len(segment) > 1:
                pygame.draw.lines(surface, BLACK, False, segment, 1)

        surface.blit(self.slug_rotated_image, self.slug_rotated_rect.topleft)
    
    def draw_sensors(self, sensors_left, sensors_right):
        """Draw sensor visualization on the Pygame surface."""
        left_sensor_pos = (
            self.cslug.x + 10 * math.cos(math.radians(self.cslug.angle - 45)),
            self.cslug.y + 10 * math.sin(math.radians(self.cslug.angle - 45))
        )
        right_sensor_pos = (
            self.cslug.x + 10 * math.cos(math.radians(self.cslug.angle + 45)),
            self.cslug.y + 10 * math.sin(math.radians(self.cslug.angle + 45))
        )

        pygame.draw.circle(self.surface, RED, (int(left_sensor_pos[0]), int(left_sensor_pos[1])), 5)
        pygame.draw.circle(self.surface, RED, (int(right_sensor_pos[0]), int(right_sensor_pos[1])), 5)

        if DEBUG_MODE:
            print(f"Left Sensor: {sensors_left}, Right Sensor: {sensors_right}")

    def create_circle_mask(self, radius):
        """Create a mask for a circular prey object."""
        surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255), (radius, radius), radius)
        return pygame.mask.from_surface(surf)
    
    def update_slug_mask(self):
        rotated_image = pygame.transform.rotate(self.slug_image, -self.cslug.angle)
        new_rect = rotated_image.get_rect(center=(self.cslug.x, self.cslug.y))

        self.cslug.mask = pygame.mask.from_surface(rotated_image)
        self.cslug.mask_topleft = new_rect.topleft

        self.slug_rotated_image = rotated_image
        self.slug_rotated_rect = new_rect
    
    def start_simulation(self):
        """Toggle simulation on/off."""
        if self.running:
            self.timer.stop()
            self.running = False
        else:
            self.timer.start(int(1000 / FPS))
            self.running = True

    def reset_simulation(self):
        """Reset the slug, prey, and odor patches."""
        if self.timer.isActive():
            self.timer.stop()
        
        self.running = False
        self.tick = 0

        self.cslug.x, self.cslug.y = WIDTH // 2, HEIGHT // 2
        self.cslug.angle = 0
        self.cslug.path = [(self.cslug.x, self.cslug.y)]

        PATCHES.fill(0)

        # Reset all prey
        for prey in self.prey_list:
            prey.respawn()

        # Reset counters
        self.cslug.hermi_counter = 0
        self.cslug.flab_counter = 0
        self.cslug.drug_counter = 0

        # Reset appetitive states
        self.cslug.app_state = 0.0
        self.cslug.app_state_switch = 0.0
        self.cslug.reward_experience = 0.0

        self.update_simulation()

    def resizeEvent(self, event):
        if self.pixmap():
            self.setPixmap(self.pixmap().scaled(
                self.size(), 
                QtCore.Qt.KeepAspectRatio, 
                QtCore.Qt.SmoothTransformation
            ))
        super().resizeEvent(event)
    
    def sizeHint(self):
        from PyQt5.QtCore import QSize
        return QSize(WIDTH, HEIGHT)
