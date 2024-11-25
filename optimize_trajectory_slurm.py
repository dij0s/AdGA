from datetime import datetime
import sys
import time
import numpy as np
from optimize_trajectory import GAManager
from mpi4py import MPI
import asyncio
import aiohttp

_print = print
def print(*args, **kwargs):
    _print("[%s]" % (datetime.now()),*args, **kwargs)

def main():
    genetic_algorithm = GAManager(population_size=10, elite_size=2, mutation_rate=0.1)

    # Split the recording into trajectories
    trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241119111936.npz")

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

    evolved_pop, fitnesses = asyncio.run(genetic_algorithm.evolve(pop, trajectory, iterations=5))

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
        np.savez("best_trajectory.npz", recvbuf)
        print(f"Time taken: {time.time() - start_time:.2f} seconds")

    MPI.Finalize()

if __name__ == "__main__":
    main()
