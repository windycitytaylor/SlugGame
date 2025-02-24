from PyQt5 import QtWidgets, uic, QtCore
import sys
from simulation_widget import SimulationWidget

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("Cyberslug_User_Interface.ui", self)

        # Create an instance of simulation widget
        simWidget = SimulationWidget()

        # Create a QGraphicsScene and add the simulation widget as a proxy widget
        scene = QtWidgets.QGraphicsScene()
        scene.addWidget(simWidget)

        # Assign scene to QGraphicsView
        self.ui.graphicsView.setScene(scene)

        self.ui.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
