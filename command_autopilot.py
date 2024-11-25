from PyQt6 import QtWidgets
import pickle, lzma

from data_collector import DataCollectionUI

class OsdNNMsgProcessor:
    def __init__(self, ga_inputs, autopilot_record_file):
        # load commands into queue
        raw_inputs = np.load(ga_inputs)['arr_0'].copy().reshape(-1, 8)
        with lzma.open(autopilot_record_file, "rb") as file:
            _, ap_positions, ap_speeds, ap_angles = pickle.load(file)

        per_rank_commands = {}

        for raw_input in raw_inputs:
            rank = int(raw_input[0])
            if rank not in per_rank_commands:
                per_rank_commands[rank] = deque([])

            per_rank_commands[rank].append((map(lambda x: int(x), raw_input[1:5])))

        # add init_speed and init_angle
        # to the per rank commands
        for rank in per_rank_commands.keys():
            init_index = rank * 10
            per_rank_commands[rank] = (
                per_rank_commands[rank],
                ap_positions[init_index],
                ap_angles[init_index]
            )

        self._per_rank_commands = per_rank_commands

        self._directions = ["forward", "back", "left", "right"]

    def process_message(self, _, data_collector):
        # current_command = self._commands.popleft()
        for command, start in (
            map(
                lambda ic: (self._directions[ic[0]], ic[1]), # map command to remote instruction
                enumerate(current_command)
            )):
            data_collector.onCarControlled(command, start)

if  __name__ == "__main__":
    import sys

    import numpy as np
    from collections import deque

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook

    app = QtWidgets.QApplication(sys.argv)

    nn_brain = OsdNNMsgProcessor(sys.argv[1], sys.argv[2])
    data_window = DataCollectionUI(nn_brain.process_message)
    data_window.show()

    app.exec()
