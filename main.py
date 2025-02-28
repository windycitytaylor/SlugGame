from PyQt5 import QtWidgets, uic, QtCore
import sys
import sluggame
import numpy as np
from simulation_widget import SimulationWidget

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("Cyberslug_User_Interface.ui", self)

        # Create an instance of simulation widget
        self.simWidget = SimulationWidget()

        # Create a QGraphicsScene and add the simulation widget as a proxy widget
        scene = QtWidgets.QGraphicsScene()
        scene.addWidget(self.simWidget)

        # Assign scene to QGraphicsView
        self.ui.graphicsView.setScene(scene)
        self.ui.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.ui.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.ui.graphicsView.setFixedSize(sluggame.WIDTH, sluggame.HEIGHT)

        # Connect buttons to function
        self.ui.SetupButton.clicked.connect(self.setup_simulation)
        self.ui.GoButton.clicked.connect(self.start_simulation)
        self.ui.StepButton.clicked.connect(self.step_simulation)

    def setup_simulation(self):
        """Reset the simulation to initial state"""
        print("Setup clicked!")
        if self.simWidget.timer.isActive():
            self.simWidget.timer.stop()
        
        self.simWidget.tick = 0
        self.simWidget.cslug.x, self.simWidget.cslug.y = self.simWidget.width // 2, self.simWidget.height // 2
        self.simWidget.cslug.angle = 0
        self.simWidget.cslug.path = [(self.simWidget.cslug.x, self.simWidget.cslug.y)]

        self.simWidget.patches = np.zeros((self.simWidget.num_odor_types, self.simWidget.pwidth, self.simWidget.pheight))

        for prey in self.simWidget.prey_list:
            prey.respawn()
        
        self.simWidget.update_simulation()
    
    def start_simulation(self):
        """Start or pause the simulation"""
        if self.simWidget.timer.isActive():
            print("Simulation paused")
            self.simWidget.timer.stop()
        else: 
            print("Simulation started")
            self.simWidget.timer.start(int(1000 / sluggame.FPS))

    def step_simulation(self):
        """Advance the simulation by one step"""
        print("Step clicked!")
        self.simWidget.update_simulation()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
