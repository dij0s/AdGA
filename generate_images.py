from os import name
import sys

import numpy as np
from collections import deque

class ImageRecorder():
    def __init__(self, ga_inputs) -> None:
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

    def start(self) -> None:
        # check if controls
        # of current rank
        # are consumed

        # queue is not consumed yet
        # play control of current rank queue
        current_controls_queue = lambda: self._per_rank_controls[self._current_rank]
        if not current_controls_queue():
            self._current_rank += 1
            # retrieve rank setup
            # as current

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

if name == "__main__":
    image_recorder = ImageRecorder(sys.argv[1])
    image_recorder.start()
