import sys
import time
import numpy as np
from optimize_trajectory import GAManager
from mpi4py import MPI
import asyncio
import aiohttp

def main():
    genetic_algorithm = GAManager(population_size=10, elite_size=2, mutation_rate=0.1)

    # Split the recording into trajectories
    trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241119111936.npz")

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    print(f"Starting rank {rank}/{size}")
    print(f"There are {len(trajectories)} trajectories")

    # Ensure the rank is within the range of trajectories
    if rank >= len(trajectories):
        print(f"Rank {rank} is out of range for the number of trajectories {len(trajectories)}")
        MPI.COMM_WORLD.Abort(1)  
        return

    trajectory = trajectories[rank]
    initial_state = {
        "init_pos": trajectory[1][0],
        "init_speed": trajectory[2][0],
        "init_rotation": trajectory[3][0],
    }

    pop = genetic_algorithm.create_population(trajectory[0], trajectory[1])

    evolved_pop, fitnesses = asyncio.run(genetic_algorithm.evolve(pop, initial_state, iterations=5))

    z = zip(evolved_pop, fitnesses)
    best = sorted(z, key=lambda x: x[1], reverse=True)[0]

    best_trajectory = best[0]
    sendbuf = (rank, np.array(best_trajectory))

    # Prepare the receive buffer on the root process
    if rank == 0:
        recvbuf = np.empty(size)
    else:
        recvbuf = None

    comm.Gather(sendbuf, recvbuf, root=0)

    if rank == 0:
        np.savez("best_trajectory.npz", recvbuf)

    MPI.Finalize()

if __name__ == "__main__":
    main()
