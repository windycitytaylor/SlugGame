from PyQt5 import QtWidgets, uic, QtCore
import sys
import os
import sluggame
import numpy as np
from simulation_widget import SimulationWidget
from config import WIDTH, HEIGHT

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        UI_FILE = os.path.join(os.path.dirname(__file__), "Cyberslug_User_Interface.ui")
        self.ui = uic.loadUi(UI_FILE, self)

        # Create an instance of simulation widget
        self.simWidget = SimulationWidget()

        # Create a QGraphicsScene and add the simulation widget as a proxy widget
        scene = QtWidgets.QGraphicsScene()
        scene.addWidget(self.simWidget)

        # Assign scene to QGraphicsView
        self.ui.graphicsView.setScene(scene)
        self.ui.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.ui.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.ui.graphicsView.setFixedSize(WIDTH, HEIGHT)

        # Connect Buttons
        self.ui.SetupButton.clicked.connect(self.setup_simulation)
        self.ui.GoButton.clicked.connect(self.simWidget.start_simulation)
        self.ui.StepButton.clicked.connect(self.step_simulation)
        self.ui.pushButton_4.clicked.connect(self.simWidget.toggle_sensors)

        # Connect Sliders
        self.ui.horizontalSlider.valueChanged.connect(lambda value: self.update_prey_population("hermi", value))
        self.ui.horizontalSlider_2.valueChanged.connect(lambda value: self.update_prey_population("flab", value))
        self.ui.horizontalSlider_3.valueChanged.connect(lambda value: self.update_prey_population("fauxflab", value))
        self.ui.horizontalSlider_4.valueChanged.connect(self.update_simulation_speed)

        # Connect Dials
        self.ui.dial.valueChanged.connect(self.update_learning_hermi)
        self.ui.dial_2.valueChanged.connect(self.update_learning_flab)
        self.ui.dial_3.valueChanged.connect(self.update_learning_drug)

        # Initialize sensor visibility
        self.sensors_visible = False
        self.update_UI()

    def setup_simulation(self):
        """Reset the simulation to initial state"""
        self.simWidget.reset_simulation()
        self.update_UI()
    

    def step_simulation(self):
        """Advance the simulation by one step"""
        self.simWidget.update_simulation()

    def update_prey_population(self, prey_type, value):
        """Update prey population dynamically based on type."""
        print(f"{prey_type} population set to: {value}")

        if prey_type == "hermi":
            self.simWidget.hermi_population = value
        elif prey_type == "flab":
            self.simWidget.flab_population = value
        elif prey_type == "fauxflab":
            self.simWidget.fauxflab_population = value

        self.simWidget.reset_prey_population()
        self.update_UI()

    def update_simulation_speed(self, value):
        """Adjust simulation speed using the slider."""
        self.simWidget.simulation_speed = max(1,value)
        print(f"Simulation speed set to: {self.simWidget.simulation_speed}")
        
        if self.simWidget.timer.isActive():
            self.simWidget.timer.start(int(1000 / self.simWidget.simulation_speed))

    def update_learning_hermi(self, value):
        """Adjust hermi learning parameter."""
        print(f"Learning Hermi set to: {value}")
        self.simWidget.cslug.alpha_hermi = value / 100  # Normalize

    def update_learning_flab(self, value):
        """Adjust flab learning parameter."""
        print(f"Learning Flab set to: {value}")
        self.simWidget.cslug.alpha_flab = value / 100  # Normalize

    def update_learning_drug(self, value):
        """Adjust drug learning parameter."""
        print(f"Learning Drug set to: {value}")
        self.simWidget.cslug.alpha_drug = value / 100  # Normalize

    def update_UI(self):
        """Update UI labels with real-time values."""
        # Simulation ticks
        self.ui.TicksOutput.setText(str(self.simWidget.tick))
        
        # Somatic map
        self.ui.lineEdit_16.setText(str(round(self.simWidget.cslug.somatic_map, 2)))

        # Incentive
        self.ui.lineEdit_15.setText(str(round(self.simWidget.cslug.incentive, 2)))

        # Appetitive State & Switch
        self.ui.lineEdit_10.setText(str(round(self.simWidget.cslug.app_state, 2)))
        self.ui.lineEdit_14.setText(str(round(self.simWidget.cslug.app_state_switch, 2)))

        # Prey Encounters (Hermi, Flab, Faux-Flab)
        self.ui.lineEdit_17.setText(str(self.simWidget.cslug.hermi_counter))
        self.ui.lineEdit_18.setText(str(self.simWidget.cslug.flab_counter))
        self.ui.lineEdit_19.setText(str(self.simWidget.cslug.drug_counter))

        # Betaine Sensor Values
        self.ui.lineEdit.setText(str(round(self.simWidget.cslug.sns_odors_left[0], 2)))
        self.ui.lineEdit_2.setText(str(round(self.simWidget.cslug.sns_odors_right[0], 2)))
        self.ui.lineEdit_3.setText(str(round(self.simWidget.cslug.sns_odors[0], 2)))

        # Hermi Sensor Values
        self.ui.lineEdit_7.setText(str(round(self.simWidget.cslug.sns_odors_left[1], 2)))
        self.ui.lineEdit_8.setText(str(round(self.simWidget.cslug.sns_odors_right[1], 2)))
        self.ui.lineEdit_9.setText(str(round(self.simWidget.cslug.sns_odors[1], 2)))
                                   
        # Flab Sensor Values
        self.ui.lineEdit_11.setText(str(round(self.simWidget.cslug.sns_odors_left[2], 2)))
        self.ui.lineEdit_12.setText(str(round(self.simWidget.cslug.sns_odors_right[2], 2)))
        self.ui.lineEdit_13.setText(str(round(self.simWidget.cslug.sns_odors[2], 2)))
                                    
        # Learning Variables
        self.ui.lineEdit_4.setText(str(round(self.simWidget.cslug.Vh, 2)))
        self.ui.lineEdit_6.setText(str(round(self.simWidget.cslug.Vf, 2)))

        # Recursively update UI
        QtCore.QTimer.singleShot(100, self.update_UI)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
