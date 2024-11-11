import math
import pickle, lzma

from random import random, randint
from functools import reduce

import numpy as np
import more_itertools

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
        controls, positions = self._load_record(record_file)

        # split the data into individual trajectories
        controls = self._split_to_subarrays(controls, self.frames_per_trajectory)
        positions = self._split_to_subarrays(positions, self.frames_per_trajectory)

        return list(zip(controls, positions))

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

    def evolve(self, population, iterations):
        """
        Evolve the population for a given number of iterations
        """

        for _ in range(iterations):
            # Simluate the population to get the positions
            simulation_results = [
                self._simulate([x for x, _ in individual])
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

    def tournament_selection(self, population, fitnesses, k=5):
        """
        Select the best individual among k randomly selected individuals
        """

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

    def _simulate(self, controls):
        """
        From a sequence of controls, simulate the car and return the position at each frame
        """

        # TODO: call the simulation...
        positions = [[randint(-10, 10), randint(-20, 20)] for _ in controls]
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
                lambda res, sensor: ([*res[0], sensor.current_controls], [*res[1], [sensor.car_position[0], sensor.car_position[2]]]),
                pickle.load(file),
                ([], [])
            )
        
    def _split_to_subarrays(self, array, n):
        return [array[i:i + n] for i in range(0, len(array), n)]

genetic_algorithm = GAManager(population_size=10)

trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241106093055.npz")
for trajectory in trajectories:
    pop = genetic_algorithm.create_population(trajectory[0], trajectory[1], n=10, p=0.2)

    evolved_pop, fitnesses = genetic_algorithm.evolve(pop, 10)

    z = zip(evolved_pop, fitnesses)
    best = sorted(z, key=lambda x: x[1], reverse=True)[0]
    print(best)
