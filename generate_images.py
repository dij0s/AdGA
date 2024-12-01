import sys

import numpy as np
from collections import deque
from multiprocessing import Queue

from ursina import Ursina
from ursina.prefabs.tooltip import Quat

from simulator import Simulator

class ImageRecorder():
    def __init__(self, ga_inputs, ursina_callback) -> None:
        self._ursina_callback = ursina_callback

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
            per_rank_controls[rank].append(map(int, raw_input[1:5]))

        self._per_rank_controls = per_rank_controls
        self._per_rank_setup = per_rank_setup

        self._max_rank = max_rank

    def start(self):
        # check if controls
        # of current rank
        # are consumed
        self.current_rank = 0
        current_controls_queue = lambda n: self._per_rank_controls.get(n, None)

        simulation_queue = Queue()
        simulation_data = []

        def play_trajectory():
            if current_controls_queue(self.current_rank):
                # there are controls
                # to be played still
                current_controls = current_controls_queue(self.current_rank)

                # queue is not consumed yet, play
                # controls of current rank queue
                current_trajectory_controls = deque([list(cs) for cs in current_controls])
                current_trajectory_setup = self._per_rank_setup[self.current_rank]

                simulation.play(current_trajectory_controls, current_trajectory_setup)
                print(f"[LOG] Controls sent to simulator (rank {self.current_rank})")

                self.current_rank += 1
            else:
                simulation.stop()

                simulation_data = simulation_queue.get()
                print([s.image for s in simulation_data])

        simulation = Simulator(
            simulation_queue=simulation_queue,
            ursina_callback=self._ursina_callback,
            play_callback=play_trajectory,
            **self._per_rank_setup[0]
        )
        print("[LOG] Created simulator instance")


if __name__ == "__main__":
    ursina_app = Ursina(size=(320, 256))
    def ursina_callback():
        print("[LOG] Killing Ursina application..")
        ursina_app.destroy()

    image_recorder = ImageRecorder(sys.argv[1], ursina_callback)
    image_recorder.start()

    # Run Ursina event loop
    print("[LOG] Starting the Ursina event loop..")
    ursina_app.run()
