import sys

import numpy as np
from collections import deque
from multiprocessing import Queue

from ursina import Ursina

from simulator import Simulator

class ImageRecorder():
    def __init__(self, ga_inputs, ursina_callback) -> None:
        self._ursina_callback = ursina_callback
        self._current_rank = 0

        raw_inputs = np.load(ga_inputs)['arr_0'].copy().reshape(-1, 10)

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
                    "init_rotation": float(raw_input[9])
                }

            # parse raw inputs to
            # only get controls
            per_rank_controls[rank] = [*per_rank_controls[rank], map(int, raw_input[1:5])]

        # parse the dict into a
        # consummable queue
        # for each rank
        self._per_rank_controls = per_rank_controls
        self._per_rank_setup = per_rank_setup

        self._max_rank = max_rank

    def start(self) -> list:
        # check if controls
        # of current rank
        # are consumed
        current_controls_queue = lambda: self._per_rank_controls[self._current_rank]
        simulation_data = []

        while current_controls_queue():
            # queue is not consumed yet play
            # controls of current rank queue
            current_trajectory_controls = [list(cs) for cs in current_controls_queue()]
            current_trajectory_setup = self._per_rank_setup[self._current_rank]

            simulation_queue = Queue()

            simulation = Simulator(
                controls=current_controls_queue,
                simulation_queue=simulation_queue,
                ursina_callback=self._ursina_callback,
                **current_trajectory_setup
            )
            print(f"[LOG] Simulator instance created (rank {self._current_rank})")
            simulation.start()

            simulation_data.append(simulation_queue.get())

        print("[LOG] All trajectories are consumed.")
        return simulation_data
        # map command to remote instruction
        # for command, start in (
        #     map(
        #         lambda ic: (self._directions[ic[0]], ic[1]),
        #         enumerate(current_command)
        #     )):
        #     # run each command in
        #     # controls queue
        #     data_collector.onCarControlled(command, start)

if __name__ == "__main__":
    ursina_app = Ursina(size=(320, 256))

    image_recorder = ImageRecorder(sys.argv[1], lambda: ursina_app.destroy())

    simulation_data = image_recorder.start()

    # Run Ursina event loop
    print("Am I here ?")
    ursina_app.run()
    print("I am..")
