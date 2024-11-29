from PyQt6 import QtWidgets
from data_collector import DataCollectionUI

import pickle, lzma
from functools import reduce

class OsdNNMsgProcessor:
    def __init__(self, ga_inputs):
        # load ga-infered controls
        raw_inputs = np.load(ga_inputs)['arr_0'].copy().reshape(-1, 8)
        # with lzma.open(autopilot_record_file, "rb") as file:
        #     _, ap_positions, ap_speeds, ap_angles = pickle.load(file)

        # put controls to play
        # for each trajectory
        # into a queue
        per_rank_controls = {}
        max_rank = 0

        for raw_input in raw_inputs:
            rank = int(raw_input[0])
            if rank not in per_rank_controls:
                max_rank = rank
                per_rank_controls[rank] = deque([])

            # parse raw inputs to
            # only get controls
            per_rank_controls[rank].append((map(lambda x: int(x), raw_input[1:5])))

        # parse the dict into a
        # consummable queue
        # for each rank
        self._per_rank_controls = per_rank_controls
        self._current_rank = 0
        self._max_rank = max_rank
        self._directions = ["forward", "back", "left", "right"]

    def process_message(self, _, data_collector):
        # check if controls
        # of current rank
        # are consumed

        # queue is not consumed yet
        # play control of current rank queue
        current_controls_queue = lambda: self._per_rank_controls[self._current_rank]
        if not current_controls_queue():
            self._current_rank += 1
            # must modify car
            # position and speed ?

            # check if all ranks are consumed
            if self._current_rank > self._max_rank:
                print("All ranks are consumed. must end here.")

        current_command = current_controls_queue().popleft()

        # map command to remote instruction
        for command, start in (
            map(
                lambda ic: (self._directions[ic[0]], ic[1]),
                enumerate(current_command)
            )):
            # run each command in
            # controls queue
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
