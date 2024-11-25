from PyQt6 import QtWidgets
from data_collector import DataCollectionUI

class OsdNNMsgProcessor:
    def __init__(self, ga_inputs):
        # load commands into queue
        raw_inputs = np.load(ga_inputs)['arr_0'].copy().reshape(-1, 8)

        per_rank_commands = {}

        for raw_input in raw_inputs:
            rank = int(raw_input[0])

            if rank not in per_rank_commands:
                per_rank_commands[rank] = []

            per_rank_commands[rank].append(map(lambda x: int(x), raw_input[1:5]))
        # only take n-overlap first
        # commands to not handle overlap
        # self._commands = deque([map(lambda x: int(x), raw_input[1:5]) for raw_input in raw_inputs])
        # print(deque([raw_input[5:] for raw_input in raw_inputs]))

        print([len(per_rank_commands[rank]) for rank in per_rank_commands.keys()])
        self._directions = ["forward", "back", "left", "right"]

    def process_message(self, _, data_collector):
        current_command = self._commands.popleft()
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

    nn_brain = OsdNNMsgProcessor(sys.argv[1])
    data_window = DataCollectionUI(nn_brain.process_message)
    data_window.show()

    app.exec()
