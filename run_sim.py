from ursina import *
from PyQt6 import QtWidgets

import sys

from simulator import Simulator

ursina_app = Ursina(size=(320,256))
autopilot_app = QtWidgets.QApplication(sys.argv)

simulation = Simulator([("forward", 1), ("left", 1)] * 10, (0, 0, 4))
simulation.start()

ursina_app.run()
autopilot_app.run()

sys.exit(autopilot_app.exec())