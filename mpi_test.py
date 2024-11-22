import sys
import time
import numpy as np
from optimize_trajectory import GAManager
from mpi4py import MPI
import os


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    print("Rank: ", rank)

    # Prepare the rank to be gathered
    sendbuf = np.array(rank, dtype='i')

    # Prepare the receive buffer on the root process
    if rank == 0:
        recvbuf = np.empty(size, dtype='i')
    else:
        recvbuf = None

    # Gather the ranks to the root process
    comm.Gather(sendbuf, recvbuf, root=0)

    if rank == 0:
        print("Ranks: ", recvbuf)

    MPI.Finalize()

if __name__ == "__main__":
    main()
