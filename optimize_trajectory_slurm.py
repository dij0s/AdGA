import sys
import time
import numpy as np
from optimize_trajectory import GAManager
from mpi4py import MPI

def main():
    genetic_algorithm = GAManager(population_size=10)

    # Split the recording into trajectories
    trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241106093055.npz")

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # Ensure the rank is within the range of trajectories
    if rank >= len(trajectories):
        raise ValueError(f"Rank {rank} is out of range for the number of trajectories {len(trajectories)}")

    trajectory = trajectories[rank]
    initial_state = {
        "init_pos": trajectory[1][0],
        "init_speed": trajectory[2][0],
        "init_rotation": trajectory[3][0],
    }

    pop = genetic_algorithm.create_population(trajectory[0], trajectory[1], n=10, p=0.2)

    evolved_pop, fitnesses = genetic_algorithm.evolve(pop, 10, initial_state)

    z = zip(evolved_pop, fitnesses)
    best = sorted(z, key=lambda x: x[1], reverse=True)[0]

    # Gather the best result from all ranks (root process will collect all)
    bests = comm.gather(best, root=0)

    if rank == 0:
        print("Bests: ", bests)

if __name__ == "__main__":
    main()