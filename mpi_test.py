import sys
import time
import numpy as np
from optimize_trajectory import GAManager
from mpi4py import MPI

def main():
    MPI.Init()
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    print("Rank: ", rank)

    ranks = []

    comm.Gather(rank, ranks, root=0)

    if rank == 0:
        print("Ranks: ", ranks)

    MPI.Finalize()

if __name__ == "__main__":
    main()