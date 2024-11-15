import math
import pickle, lzma

from random import random, randint
from functools import reduce
import time

import numpy as np
import more_itertools

import requests

class GAManager():
    """
    Following class handles the genetic algorithm
    problem with the goal of optimizing the
    autopilot's trajectory
    """

    def __init__(self, frames_per_trajectory = 10, population_size = 100):
        self.frames_per_trajectory = frames_per_trajectory
        self.population_size = population_size

    def split_recording_into_trajectories(self, record_file):
        """
        From the specified record file, split the data into individual trajectories
        of frames_per_trajectory frames
        The data is returned as a list of tuples (controls, positions)
        """

        # load the recorded data
        controls, positions, speed, angle = self._load_record(record_file)

        # split the data into individual trajectories
        controls = self.split_to_subarrays(controls, self.frames_per_trajectory)
        positions = self.split_to_subarrays(positions, self.frames_per_trajectory)
        speeds = self.split_to_subarrays(speed, self.frames_per_trajectory)
        angles = self.split_to_subarrays(angle, self.frames_per_trajectory)

        return list(zip(controls, positions, speeds, angles))

    def create_population(self, controls, positions, n, p):
        """
        Create a population of n individuals from the given controls and positions
        """

        return [
            [
                (control, position) if random() > p else (self._flip_single_bit(control), position)
                for (control, position) in zip(controls, positions)
            ]
            for _ in range(n)
        ]

    def evolve(self, population, iterations, initial_state):
        """
        Evolve the population for a given number of iterations
        """

        for _ in range(iterations):
            # Simluate the population to get the positions
            simulation_results = [
                self._simulate([x for x, _ in individual], initial_state)
                for individual in population
            ]

            positions = [
                [position for _, position in simulation_result]
                for simulation_result in simulation_results
            ]

            fitnesses = [self._fitness(positions_seq) for positions_seq in positions]

            population = simulation_results

            # initialize the next generation with the 20% best individuals
            population = self._select_elites(population, fitnesses, p=0.2)

            while len(population) < self.population_size:
                # select two good parents
                parent1 = self.tournament_selection(population, fitnesses)
                parent2 = self.tournament_selection(population, fitnesses)

                # apply crossover
                child = self._one_point_crossover(parent1, parent2)

                # apply mutation
                child = self._mutate(child, 0.1)

                population.append(child)

        return population, fitnesses

    def tournament_selection(self, population, fitnesses, k=2):
        """
        Select the best individual among k randomly selected individuals
        """

        print(len(population))
        # select k random individuals
        random_indices = [randint(0, len(population) - 1) for _ in range(k)]
        tournament_individuals = [population[i] for i in random_indices]
        tournament_fitnesses = [fitnesses[i] for i in random_indices]

        # return the best individual
        best_fitness = max(tournament_fitnesses)
        return tournament_individuals[tournament_fitnesses.index(best_fitness)]

    def _select_elites(self, population, fitnesses, p=0.2):
        """
        Select the top p individuals of the population
        """

        # sort the population by fitness
        population = [x for _, x in sorted(zip(fitnesses, population), reverse=True)]

        # keep the top p of the population
        return population[:int(p * len(population))]

    def _format_controls(self, controls):
        def format_control(control):
            return [
                ["forward", control[0]],
                ["back", control[1]],
                ["left", control[2]],
                ["right", control[3]],
            ]

        return [format_control(control) for control in controls]

    def _simulate(self, controls, init_state):
        """
        From a sequence of controls, simulate the car and return the position at each frame
        """

        endpoint = "http://192.168.88.248:32307/api/simulate"

        data = {
            "controls": self._format_controls(controls),
            "init_pos": init_state["init_pos"],
            "init_speed": init_state["init_speed"],
            "init_rotation": init_state["init_rotation"],
        }

        positions = requests.post(endpoint, json=data)
        positions = positions.json()
        return list(zip(controls, positions))

    def _one_point_crossover(self, controls1, controls2):
        """
        Merge two sequences of controls by taking the first half of the first sequence and the second half of the second sequence
        """

        split = randint(0, len(controls1))

        return controls1[:split] + controls2[split:]
                
    def _flip_single_bit(self, control):
        """
        Flip a single bit of the control
        """

        index_to_flip = randint(0, 3)
        return tuple(
            1 - c if index == index_to_flip else c 
            for (index, c) in enumerate(control)
        )
    
    def _mutate(self, controls, p):
        """
        Apply a bit flip mutation with probability p on each control of the sequence
        """

        return [
            (control if random() > p else self._flip_single_bit(control), pos)
            for control, pos in controls
        ]

    def _fitness(self, positions):
        """
        Compute the fitness of a sequence of positions
        We define the fitness as the total travelled distance by the car, with the goal of maximizing it
        """

        def dist(p1, p2):
            return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
        return sum([dist(p1, p2) for (p1, p2) in more_itertools.pairwise(positions)])

    def _load_record(self, record_file):
        """
        Load the recorded data from the specified file
        """

        with lzma.open(record_file, "rb") as file:
            return reduce(
                lambda res, sensor: (
                    [*res[0], sensor.current_controls], 
                    [*res[1], [sensor.car_position[0], sensor.car_position[2]]],
                    [*res[2], sensor.car_speed],
                    [*res[3], sensor.car_angle]
                ),
                pickle.load(file),
                ([], [], [], [])
            )

    def split_to_subarrays(self, array, window_size=10, overlap=4):
        step_size = window_size - overlap
        return [array[i:i + window_size] for i in range(0, len(array) - window_size + 1, step_size)]

genetic_algorithm = GAManager(population_size=10)

trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241106093055.npz")

time_before = time.time()
for trajectory in trajectories[:1]:
    initial_state = {
        "init_pos": trajectory[1][0],
        "init_speed": trajectory[2][0],
        "init_rotation": trajectory[3][0],
    }
    
    pop = genetic_algorithm.create_population(trajectory[0], trajectory[1], n=10, p=0.2)

    evolved_pop, fitnesses = genetic_algorithm.evolve(pop, 10, initial_state)

    z = zip(evolved_pop, fitnesses)
    best = sorted(z, key=lambda x: x[1], reverse=True)[0]
    print(best)

