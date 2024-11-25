from datetime import datetime
import sys
import time
import numpy as np
from optimize_trajectory import GAManager
from mpi4py import MPI
import asyncio
import aiohttp
import argparse

_print = print
def print(*args, **kwargs):
    _print("[%s]" % (datetime.now()),*args, **kwargs)

def main(trajectories_file, population_size=10, elite_size=2, mutation_rate=0.1, iterations=5, output_file="best_trajectory.npz"):
    if trajectories_file is None:
        print("Gimme a trajectory file, bro")
        return

    genetic_algorithm = GAManager(population_size=population_size, elite_size=elite_size, mutation_rate=mutation_rate)

    # Split the recording into trajectories
    trajectories = genetic_algorithm.split_recording_into_trajectories(trajectories_file)

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    start_time = time.time()

    print(f"Starting rank {rank}/{size-1}")
    print(f"There are {len(trajectories)} trajectories")

    # Ensure the rank is within the range of trajectories
    if rank >= len(trajectories):
        print(f"Rank {rank} is out of range for the number of trajectories {len(trajectories)}")
        MPI.COMM_WORLD.Abort(1)  
        return

    trajectory = trajectories[rank]

    pop = genetic_algorithm.create_population(trajectory[0], trajectory[1])

    evolved_pop, fitnesses = asyncio.run(genetic_algorithm.evolve(pop, trajectory, iterations=iterations))

    z = zip(evolved_pop, fitnesses)
    best = sorted(z, key=lambda x: x[1], reverse=True)[0]

    best_trajectory = best[0]

    flattened_trajectory = np.array([
        (rank, *state, *metrics)  # Combine the tuple and the list into a single flat list
        for state, metrics in best_trajectory
    ], dtype=np.float32)

    print("best_trajectory", best_trajectory)
    sendbuf_size = flattened_trajectory.size
    sendbuf = flattened_trajectory.flatten()

    # Prepare the receive buffer on the root process
    if rank == 0:
        recvbuf = np.empty(size * sendbuf_size, dtype=np.float32)
    else:
        recvbuf = None

    comm.Gather(sendbuf, recvbuf, root=0)

    if rank == 0:
        recvbuf = recvbuf.reshape(size, -1)  # Each row corresponds to one process's data
        np.savez(output_file, recvbuf)
        print(f"Time taken: {time.time() - start_time:.2f} seconds")

    MPI.Finalize()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AdGA")
    parser.add_argument("--population_size", "-p", type=int, default=10, help="Population size (number of individuals in each generation)")
    parser.add_argument("--elite_size", "-e", type=int, default=2, help="Elite size (number of top individuals to keep)")
    parser.add_argument("--mutation_rate", "-m", type=float, default=0.1, help="Mutation rate (probability of mutation)")
    parser.add_argument("--iterations", "-i", type=int, default=5, help="Number of iterations to run the genetic algorithm")
    parser.add_argument("--output-file", "-o", type=str, default="best_trajectory.npz", help="Output file name")
    parser.add_argument("--trajectories-file", "-t", type=str, help="Input trajectories records file name", required=True)
    args = parser.parse_args()

    main(
        trajectories_file=args.trajectories_file,
        population_size=args.population_size,
        elite_size=args.elite_size,
        mutation_rate=args.mutation_rate,
        iterations=args.iterations,
        output_file=args.output_file
    )
