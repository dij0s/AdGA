import collections
from datetime import datetime
import math
import pickle, lzma

from random import random, randint
from functools import reduce
import time

import numpy as np
import more_itertools

import requests
import asyncio
import aiohttp

import traceback

_print = print
def print(*args, **kwargs):
    _print("[%s]" % (datetime.now()),*args, **kwargs)

class GAManager():
    """
    Following class handles the genetic algorithm
    problem with the goal of optimizing the
    autopilot's trajectory
    """

    def __init__(self, frames_per_trajectory = 10, population_size = 100, elite_size = 20, mutation_rate = 0.1, max_concurrent_requests = 10):
        if frames_per_trajectory < 2:
            raise ValueError("frames_per_trajectory must be at least 2")

        if population_size < 2:
            raise ValueError("population_size must be at least 2")

        self.frames_per_trajectory = frames_per_trajectory
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.elite_percentage = elite_size / population_size
        self.max_concurrent_requests = max_concurrent_requests
        self.sim_memo = {}


    def split_recording_into_trajectories(self, record_file, split_window_size=10, split_overlap=4):
        """
        From the specified record file, split the data into individual trajectories
        of frames_per_trajectory frames
        The data is returned as a list of tuples (controls, positions)
        """

        # load the recorded data
        controls, positions, speed, angle = self._load_record(record_file)

        # convert the positions to a 3D format (y is the vertical axis)
        positions = [(x, 0, y) for x, y in positions]

        # split the data into individual trajectories
        controls = self.split_to_subarrays(controls, window_size=split_window_size, overlap=split_overlap)
        positions = self.split_to_subarrays(positions, window_size=split_window_size, overlap=split_overlap)
        speeds = self.split_to_subarrays(speed, window_size=split_window_size, overlap=split_overlap)
        angles = self.split_to_subarrays(angle, window_size=split_window_size, overlap=split_overlap)

        return list(zip(controls, positions, speeds, angles))

    def create_population(self, controls, positions):
        """
        Create a population of n individuals from the given controls and positions
        """

        return [
            [
                (control, position) if random() > self.mutation_rate else (self._flip_single_bit(control), position)
                for (control, position) in zip(controls, positions)
            ]
            for _ in range(self.population_size)
        ]

    async def evolve(self, population, ref_trajectory, iterations=100):
        """
        Evolve the population for a given number of iterations
        """

        initial_state = {
            "init_pos": ref_trajectory[1][0],
            "init_speed": ref_trajectory[2][0],
            "init_rotation": ref_trajectory[3][0],
        }

        pop_hash = hash(str(population))
        print(f"Starting evolution for population {pop_hash}, {len(population)} individuals, {iterations} iterations")

        best_fitnesses = []
        for _ in range(iterations):
            print(f"Starting iteration {_ + 1}/{iterations} for population {pop_hash}")

            # create a semaphore to limit the number of concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)

            # Simulate the population to get the positions
            simulation_results = await asyncio.gather(
                *[self._simulate([x for x, _ in individual], initial_state, semaphore) for individual in population]
            )

            print("SIMULATION_RESULTS")
            print(simulation_results)

            positions = [
                [record["car_position"] for _, record in simulation_result]
                for simulation_result in simulation_results
            ]

            #fitnesses = [self._fitness(positions_seq) for positions_seq in positions]
            fitnesses = [self._fitness2(positions_seq, ref_trajectory) for positions_seq in positions]
            best_fitnesses.append(max(fitnesses))

            population = simulation_results

            # initialize the next generation with the top best individuals
            population = self._select_elites(population, fitnesses)

            while len(population) < self.population_size:
                # select two good parents
                parent1 = self.tournament_selection(population, fitnesses)
                parent2 = self.tournament_selection(population, fitnesses)

                # apply crossover
                child = self._one_point_crossover(parent1, parent2)

                # apply mutation
                child = self._mutate(child, 0.1)

                population.append(child)

        return population, fitnesses, best_fitnesses

    def tournament_selection(self, population, fitnesses, k=2):
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

    def _select_elites(self, population, fitnesses):
        """
        Select the top p individuals of the population
        """

        # sort the population by fitness
        population = [x for _, x in sorted(zip(fitnesses, population), reverse=True)]

        p = self.elite_percentage

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

    async def _simulate(self, controls, init_state, semaphore, retries=20):
        """
        From a sequence of controls, simulate the car and return the position at each frame
        """

        controls_hash = hash(str(controls))
        print("hash: ", controls_hash)
    
        endpoint = "http://192.168.88.248:30333/api/route"

        data = {
            "controls": self._format_controls(controls),
            "init_pos": init_state["init_pos"],
            "init_speed": init_state["init_speed"],
            "init_rotation": init_state["init_rotation"],
        }

        headers = {
            "Connection": "close",
        }

        async with semaphore:
            start_time = time.time()

            if controls_hash in self.sim_memo:
                print(f"Found memoized simulation for controls {controls_hash}")
                return self.sim_memo[controls_hash]       

            print(f"Sending request for controls {controls_hash} ...")
            for retry in range(retries):
                try: 
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(35)) as session:
                        async with session.post(endpoint, json=data, headers=headers) as response:
                            if response.status != 200:
                                print(f"HTTP error received for {controls_hash} with status {response.status} with body {await response.text()}")
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=response.reason)

                            sensing = await response.json()

                            # TODO: This is stupid, we shouldn't receive an error as a string here, but something is broken 
                            # and we already took three hours looking for it and we're tired so this will have to do for now
                            if isinstance(sensing, str):
                                print(f"Received error for controls {controls_hash}: {sensing}")
                                raise Exception(sensing)

                            end_time = time.time() - start_time
                            print(f"Received response for controls {controls_hash} in {end_time:.2f} seconds after {retry} retries")
                            
                            result = list(zip(controls, sensing))
                            self.sim_memo[controls_hash] = result

                            return result
                except Exception as e:
                    print(f"Attempt {retry+ 1} failed for controls {controls_hash}: {e}")
                    #print(traceback.format_exc())
                    if isinstance(e, aiohttp.ClientResponseError):
                        print(f"HTTP error {e.status}: {e.message}")
                        if e.status == 500:
                            error_details = e.message
                            print(f"Error details: {error_details}")
                    if retry == retries - 1:
                        raise
                    random_offset = randint(500, 5000) / 1000
                    await asyncio.sleep(2 ** min(4, retry))  # Exponential backoff, with a maximum of 16 seconds


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
            try:
                return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            except:
                print("GLOUPS")
                print("p1", p1)
                print("p2", p2)
                raise
        
        return sum([dist(p1, p2) for (p1, p2) in more_itertools.pairwise(positions)])

    def _fitness2(self, positions, ref_trajectory):
        """
        Compute the fitness of a sequence of positions
        We define the fitness as the difference between the total travelled distance by the reference and the simulation,
        with the goal of maximizing it
        """

        def dist(p1, p2):
            return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

        reference_positions = ref_trajectory[1]

        total_frames = len(positions)
        sim_cum_distances = [ 0 ] * total_frames 
        ref_cum_distances = [ 0 ] * total_frames

        # compute the cumulative distances for the simulation and the reference
        for i in range(1, total_frames):
            sim_cum_distances[i] = sim_cum_distances[i - 1] + dist(positions[i - 1], positions[i])
            ref_cum_distances[i] = ref_cum_distances[i - 1] + dist(reference_positions[i - 1], reference_positions[i])

        sim_total_distance = sim_cum_distances[-1]
        ref_total_distance = ref_cum_distances[-1]

        # find at which (whole) simulation frame we've reached the same distance as the reference
        reach_frame = -1
        for i, distance in enumerate(sim_cum_distances):
            if sum(sim_cum_distances[:i]) >= ref_total_distance:
                reach_frame = i
                break

        r = 0.0
        if reach_frame == -1:
            # the simulation took longer to reach the same distance as the reference
            # extrapolate the total (fraction) frames it would have taken to reach the same distance as the reference

            r = total_frames * (sim_total_distance / ref_total_distance)
        else:
            # the simulation travelled more distance than the reference
            # interpolate the (fraction) frame at which we've reached the same distance as the reference

            if sim_total_distance == 0:
                print("FUCK")
                print(sim_cum_distances)
                print(positions)

            reach_frame_distance = sum(sim_cum_distances)
            over_distance = reach_frame_distance - ref_total_distance
            over_distance_ratio = 1 if sim_total_distance == 0 else over_distance / sim_total_distance
            over_distance_frame = reach_frame + over_distance_ratio * total_frames

            r = over_distance_frame

        # convert the distance difference to a fitness value
        # total^2 - r^2 so that the fitness gets greater as the simulation gets better time-wise, with the goal of maximizing it
        return total_frames * total_frames - r * r

    def _load_record(self, record_file):
        """
        Load the recorded data from the specified file
        """

        with lzma.open(record_file, "rb") as file:
            return pickle.load(file)

    def split_to_subarrays(self, array, window_size=10, overlap=4):
        step_size = window_size - overlap
        return [array[i:i + window_size] for i in range(0, len(array) - window_size + 1, step_size)]


if __name__ == "__main__":
    start_time = time.time()

    genetic_algorithm = GAManager(population_size=10, elite_size=2, mutation_rate=0.1, max_concurrent_requests=3)

    trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241119111936.npz", split_window_size=10, split_overlap=5)

    time_before = time.time()
    for trajectory in trajectories[:4]:
        initial_state = {
            "init_pos": trajectory[1][0],
            "init_speed": trajectory[2][0],
            "init_rotation": trajectory[3][0],
        }
        
        pop = genetic_algorithm.create_population(trajectory[0], trajectory[1])

        evolved_pop, fitnesses = asyncio.run(genetic_algorithm.evolve(pop, trajectory, iterations=5))

        z = zip(evolved_pop, fitnesses)
        best = sorted(z, key=lambda x: x[1], reverse=True)[0]
        print(best)

    print(f"Total time taken:  {time.time() - start_time} seconds")

