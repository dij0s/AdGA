from simulator import Simulator

import sys
from PyQt6 import QtWidgets

app = QtWidgets.QApplication(sys.argv)

simulation = Simulator([("forward", 1), ("left", 1)] * 10, (0, 0, 4))
simulation.start()

sys.exit(app.exec())