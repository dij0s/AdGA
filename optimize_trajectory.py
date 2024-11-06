import pickle, lzma

from random import random, randint
from functools import reduce

import numpy as np

class GAManager():
    """
    Following class handles the genetic algorithm
    problem with the goal of optimizing the
    autopilot's trajectory
    """

    def __init__(self, record_file, frames_per_trajectory = 10):
        # load the recorded data
        controls, positions = self._load_record(record_file)

        # split the data into
        # individual trajectories
        controls = self._split_to_subarrays(controls, frames_per_trajectory)
        positions = self._split_to_subarrays(positions, frames_per_trajectory)
        
        # run a genetic algorithm
        # on each trajectory
        for controls_per_trajectory, positions_per_trajectory in zip([controls[0]], [positions[0]]):
            # create the first population
            population_size = 100
            population_controls = self.create_population(controls_per_trajectory, positions_per_trajectory, n=population_size, p=0.2)

    def create_population(self, controls, positions, n, p):
        # current controls is a series
        # of inputs given to the car
        # we might apply randomness
        # to those controls
        
        # def compute_position

        def flip_single_bit(control):
            index_to_flip = randint(0, 3)
            return tuple(
                    c if index != index_to_flip else 1 - c 
                    for (index, c) in enumerate(control)
                )

        return [
            [
                (control, position) if random() > p else flip_single_bit(control)
                for (control, position) in zip(controls, positions)
            ]
            for _ in range(n)
        ]

    def _load_record(self, record_file):
        with lzma.open(record_file, "rb") as file:
            return reduce(
                lambda res, sensor: ([*res[0], sensor.current_controls], [*res[1], [sensor.car_position[0], sensor.car_position[2]]]),
                pickle.load(file),
                ([], [])
            )
        
    def _split_to_subarrays(self, array, n):
        return [array[i:i + n] for i in range(0, len(array), n)]

genetic_algorithm = GAManager("records/record_241106093055.npz")
