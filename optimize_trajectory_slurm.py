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

def main(trajectories_file, population_size=10, elite_size=2, mutation_rate=0.1, iterations=5, output_file="best_trajectory.npz",
         split_window_size=10, split_overlap=5, max_concurrent_requests=10):

    if trajectories_file is None:
        print("Gimme a trajectory file, bro")
        return

    print(f"Running with population_size={population_size}, elite_size={elite_size}, mutation_rate={mutation_rate}, iterations={iterations}, output_file={output_file}")

    genetic_algorithm = GAManager(
        population_size=population_size, 
        elite_size=elite_size, 
        mutation_rate=mutation_rate, 
        frames_per_trajectory=split_window_size,
        max_concurrent_requests=max_concurrent_requests
    )

    # Split the recording into trajectories
    trajectories = genetic_algorithm.split_recording_into_trajectories(trajectories_file, split_window_size, split_overlap)

    print(f"Loaded {len(trajectories)} trajectories from {trajectories_file}")

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    start_time = time.time()

    print(f"Starting rank {rank}/{size-1}")
    print(f"There are {len(trajectories)} trajectories")

    # Ensure the rank is within the range of trajectories
    if rank >= len(trajectories):
        print(f"Rank {rank} is out of range for the number of trajectories {len(trajectories)}")
        exit()

    trajectory = trajectories[rank]

    pop = genetic_algorithm.create_population(trajectory[0], trajectory[1])

    evolved_pop, fitnesses, best_fitnesses = asyncio.run(genetic_algorithm.evolve(pop, trajectory, iterations=iterations))

    z = zip(evolved_pop, fitnesses)
    best = sorted(z, key=lambda x: x[1], reverse=True)[0]

    best_trajectory = best[0]

    def flatten_records(rec):
        return [
            rec["car_speed"],
            *rec["car_position"],
            rec["car_angle"]
        ]

    flattened_trajectory = np.array([
        (rank, *controls, *flatten_records(records))  # Combine the rank, controls and car readings into one float array 
        for controls, records in best_trajectory
    ], dtype=np.float32)

    print("Found best trajectory: ", best_trajectory)
    t_sendbuf_size = flattened_trajectory.size
    f_sendbuf_size = len(best_fitnesses)
    t_sendbuf = flattened_trajectory.flatten()
    f_sendbuf = np.array(best_fitnesses, dtype=np.float32)
    t_recvbuf = None
    f_recvbuf = None

    # Prepare the receive buffer on the root process
    if rank == 0:
        t_recvbuf = np.empty(size * t_sendbuf_size, dtype=np.float32)
        f_recvbuf = np.empty(size * f_sendbuf_size, dtype=np.float32)

    comm.Gather(t_sendbuf, t_recvbuf, root=0)
    comm.Gather(f_sendbuf, f_recvbuf, root=0)
    
    if rank == 0:
        t_recvbuf = t_recvbuf.reshape(size, -1)  # Each row corresponds to one process's data
        np.savez(output_file, t_recvbuf)
        print(f"Time taken: {time.time() - start_time:.2f} seconds")

        f_recvbuf = f_recvbuf.reshape(size, -1) # Each row corresponds to one process's data
        for i, f in enumerate(f_recvbuf):
            print(f"Trajectory {i}: {f}")

        min_fitnesses = np.min(f_recvbuf, axis=0)
        max_fitnesses = np.max(f_recvbuf, axis=0)
        avg_fitnesses = np.mean(f_recvbuf, axis=0)

        # plot the fitnesses, with the average as a line and the min/max as a shaded region
        import matplotlib.pyplot as plt
        plt.plot(avg_fitnesses, label="Average")
        plt.fill_between(range(len(avg_fitnesses)), min_fitnesses, max_fitnesses, alpha=0.5, label="Min/Max")
        plt.legend()
        plt.xlabel("Generation")
        plt.ylabel("Fitness")
        plt.title("Fitness over time")

        plt.savefig("fitness_plot.png")


    MPI.Finalize()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AdGA")
    parser.add_argument("--population-size", "-p", type=int, default=10, help="Population size (number of individuals in each generation)")
    parser.add_argument("--elite-size", "-e", type=int, default=2, help="Elite size (number of top individuals to keep)")
    parser.add_argument("--mutation-rate", "-m", type=float, default=0.1, help="Mutation rate (probability of mutation)")
    parser.add_argument("--iterations", "-i", type=int, default=5, help="Number of iterations to run the genetic algorithm")
    parser.add_argument("--output-file", "-o", type=str, default="best_trajectory.npz", help="Output file name")
    parser.add_argument("--trajectories-file", "-t", type=str, help="Input trajectories records file name", required=True)
    parser.add_argument("--split-window-size", "-w", type=int, default=10, help="Size of each sub-trajectory to split the trajectories")
    parser.add_argument("--split-overlap", "-s", type=int, default=5, help="Overlap of sub-trajectories")
    parser.add_argument("--max-concurrent-requests", "-r", type=int, default=10, help="Maximum number of concurrent requests to the simulation server")
    args = parser.parse_args()

    main(
        trajectories_file=args.trajectories_file,
        population_size=args.population_size,
        elite_size=args.elite_size,
        mutation_rate=args.mutation_rate,
        iterations=args.iterations,
        output_file=args.output_file,
        split_window_size=args.split_window_size,
        split_overlap=args.split_overlap,
        max_concurrent_requests=args.max_concurrent_requests
    )
