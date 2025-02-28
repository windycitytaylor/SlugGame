# simulation_widget.py
from PyQt5 import QtCore, QtGui, QtWidgets
import pygame, math, random, numpy as np
import sluggame

# Make sure Pygame is initialized (for offscreen surfaces)
pygame.init()

class SimulationWidget(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.width, self.height = sluggame.WIDTH, sluggame.HEIGHT
        #self.setFixedSize(self.width, self.height)
        # Create an offscreen Pygame surface for rendering
        self.surface = pygame.Surface((self.width, self.height))
        self.clock = pygame.time.Clock()

        self.cslug = sluggame.Cyberslug()

        self.hermi_population = 4 
        self.flab_population = 4
        self.fauxflab_population = 4

        self.prey_list = []
        self.reset_prey_population()

        # Set up odor patch parameters locally (or use sluggame.patches if you prefer)
        self.num_odor_types = sluggame.num_odor_types
        self.pwidth, self.pheight = sluggame.pwidth, sluggame.pheight
        self.patches = np.zeros((self.num_odor_types, self.pwidth, self.pheight))
        self.scale = self.pwidth / self.width

        # Set up a QTimer to update the simulation at roughly FPS rate
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.running = False

        self.tick = 0
        self.total_ticks = 1000000
        
        self.show_sensors = False
    
    def reset_prey_population(self):
        """Rebuild the prey list based on slider values."""
        self.prey_list.clear()

        for _ in range(self.hermi_population):
            self.prey_list.append(sluggame.Prey(random.randint(0, self.width), random.randint(0, self.height), sluggame.CYAN, sluggame.hermi_odorlist))
        for _ in range(self.flab_population):
            self.prey_list.append(sluggame.Prey(random.randint(0, self.width), random.randint(0, self.height), sluggame.PINK, sluggame.flab_odorlist))
        for _ in range(self.fauxflab_population):
            self.prey_list.append(sluggame.Prey(random.randint(0, self.width), random.randint(0, self.height), sluggame.YELLOW, sluggame.drug_odorlist))
    
    def toggle_sensors(self):
        """Toggle the visibility of sensor visualization."""
        self.show_sensors = not self.show_sensors
        print(f"Sensors visualization: {'ON' if self.show_sensors else 'OFF'}")
        self.update_simulation()

    def update_simulation(self):
        # Clear the offscreen surface
        self.surface.fill(sluggame.WHITE)
        self.tick += 1

        # Update odor patches: let each prey deposit its odor
        for prey in self.prey_list:
            sluggame.SetPatch(prey.x, prey.y, prey.odorlist, self.patches)
        sluggame.UpdateOdors(self.patches)

        # Move and draw prey onto the offscreen surface
        for prey in self.prey_list:
            prey.move()
            prey.draw(self.surface)

        # Slug encounter and movement logic
        encounter = "none"
        for prey in self.prey_list:
            if math.hypot(prey.x - self.cslug.x, prey.y - self.cslug.y) < 10:
                if prey.color == sluggame.CYAN:
                    encounter = "hermi"
                elif prey.color == sluggame.PINK:
                    encounter = "flab"
                elif prey.color == sluggame.YELLOW:
                    encounter = "drug"
                prey.respawn()

        sensors_left, sensors_right = sluggame.Sensors(self.cslug.x, self.cslug.y, self.cslug.angle, self.patches)

        turn_angle = self.cslug.update(sensors_left, sensors_right, encounter)
        self.cslug.angle -= turn_angle

        prev_x, prev_y = self.cslug.x, self.cslug.y
        new_x = (self.cslug.x + self.cslug.speed * math.cos(math.radians(self.cslug.angle))) % self.width
        new_y = (self.cslug.y + self.cslug.speed * math.sin(math.radians(self.cslug.angle))) % self.height
        if abs(new_x - prev_x) > self.width / 2 or abs(new_y - prev_y) > self.height/2:
            self.cslug.path.append(None)
        self.cslug.x, self.cslug.y = new_x, new_y
        self.cslug.path.append((self.cslug.x, self.cslug.y))

        self.cslug.draw(self.surface)

        if self.show_sensors:
            self.draw_sensors(sensors_left, sensors_right)

        # Convert the offscreen surface to a QImage and display it
        image_str = pygame.image.tostring(self.surface, 'RGB')
        qimage = QtGui.QImage(image_str, self.width, self.height, QtGui.QImage.Format_RGB888)
        scaled_image = qimage.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setPixmap(QtGui.QPixmap.fromImage(scaled_image))
        self.clock.tick(sluggame.FPS)
    
    def draw_sensors(self, sensors_left, sensors_right):
        """Draw sensor visualization on the Pygame surface."""
        left_sensor_pos = (self.cslug.x + 10 * math.cos(math.radians(self.cslug.angle + 45)),
                           self.cslug.y + 10 * math.sin(math.radians(self.cslug.angle + 45)))
        right_sensor_pos = (self.cslug.x + 10 * math.cos(math.radians(self.cslug.angle - 45)),
                            self.cslug.y + 10 * math.sin(math.radians(self.cslug.angle - 45)))

        pygame.draw.circle(self.surface, sluggame.RED, (int(left_sensor_pos[0]), int(left_sensor_pos[1])), 5)
        pygame.draw.circle(self.surface, sluggame.RED, (int(right_sensor_pos[0]), int(right_sensor_pos[1])), 5)

        print(f"Left Sensor: {sensors_left}, Right Sensor: {sensors_right}")
    
    def start_simulation(self):
        if self.running:
            self.timer.stop()
            self.running = False
        else:
            self.timer.start(int(1000 / sluggame.FPS))
            self.running = True

    def reset_simulation(self):
        if self.timer.isActive():
            self.timer.stop()
        
        self.running = False
        self.tick = 0
        self.cslug.x, self.cslug.y = self.width // 2, self.height // 2
        self.cslug.angle = 0
        self.cslug.path = [(self.cslug.x, self.cslug.y)]
        self.patches.fill(0)

        for prey in self.prey_list:
            prey.respawn()

        self.cslug.hermi_counter = 0
        self.cslug.flab_counter = 0
        self.cslug.drug_counter = 0

        self.cslug.app_state = 0.0
        self.cslug.app_state_switch = 0.0
        self.cslug.rewardExperience = 0.0

        self.update_simulation()


    def resizeEvent(self, event):
        if self.pixmap():
            self.setPixmap(self.pixmap().scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        super().resizeEvent(event)
    
    def sizeHint(self):
        from PyQt5.QtCore import QSize
        return QSize(sluggame.WIDTH, sluggame.HEIGHT)
