from PyQt6.QtCore import QTimer
from PyQt6 import QtWidgets

import sys

from collections import deque
from rallyrobopilot import *

class Simulator(QtWidgets.QMainWindow):
    """
    Simulate a series of controls
    on a car instance through
    the network
    """
    def __init__(self, controls):
        self._controls = deque(controls);
        self._recorded_data = []

    def run(self):
        app = QtWidgets.QApplication(sys.argv)

        # create network interface
        self.network_interface = NetworkDataCmdInterface(self._collect_data)
        # connect to socket
        self.timer = QTimer()
        self.timer.timeout.connect(self.network_interface.recv_msg)
        self.timer.start(25)
        # TODO: RETURN DATA AT THE END
        app.exec()

    def get_recorded_data(self):
        return self._recorded_data

    def _collect_data(self, message):
        self._recorded_data.append(message)
        
        current_control = self._controls.popleft()
        print(current_control)
        # TODO: HANDLE IF THERE IS NONE LEFT
        for index, (command, start) in enumerate(current_control):
            print(index, command)
            self._send_command(command, start)

    def _send_command(self, direction, start):
        command_types = ["release", "push"]
        self.network_interface.send_cmd(command_types[start] + " " + direction+";")