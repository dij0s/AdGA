from PyQt6 import QtWidgets
from data_collector import DataCollectionUI

import pickle, lzma
from functools import reduce

class OsdNNMsgProcessor:
    def __init__(self, ga_inputs):
        # load ga-infered controls
        raw_inputs = np.load(ga_inputs)['arr_0'].copy().reshape(-1, 10)
        print(raw_inputs.shape)
        # with lzma.open(autopilot_record_file, "rb") as file:
        #     _, ap_positions, ap_speeds, ap_angles = pickle.load(file)

        # put controls to play
        # for each trajectory
        # into a queue
        per_rank_controls = {}
        per_rank_setup = {}
        max_rank = 0

        for raw_input in raw_inputs:
            rank = int(raw_input[0])
            if rank not in per_rank_controls:
                max_rank = rank
                per_rank_controls[rank] = deque([])
                # append init_position, init_speed
                # and init_angle to current rank
                per_rank_setup[rank] = {
                    "init_speed": float(raw_input[5]),
                    "init_position": tuple(raw_input[6:9]),
                    "init_angle": float(raw_input[9])
                }

            # parse raw inputs to
            # only get controls
            per_rank_controls[rank].append(map(int, raw_input[1:5]))

        # parse the dict into a
        # consummable queue
        # for each rank
        self._per_rank_controls = per_rank_controls
        self._per_rank_setup = per_rank_setup
        self._current_rank = 0
        self._max_rank = max_rank
        self._directions = ["forward", "back", "left", "right"]

    def process_message(self, _, data_collector):


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
