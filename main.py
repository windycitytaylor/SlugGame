from PyQt5 import QtWidgets, uic
import sys
from simulation_widget import SimulationWidget

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Cyberslug_User_Interface.ui", self)  # Load Katya’s UI file
        # Assume your UI file has a placeholder QGraphicsView or QWidget named "graphicsView"
        self.simulationWidget = SimulationWidget(self)
        self.graphicsView.setWidget(self.simulationWidget)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
