#!/bin/bash
#SBATCH --job-name=ga_optimization
#SBATCH --output=ga_optimization_%A_%a.out
#SBATCH --error=ga_optimization_%A_%a.err
#SBATCH --nodelist=calypso[0,1]             # Use only these 3 nodes
#SBATCH --nodes=2                             # Use 3 nodes (each node will run some jobs)
#SBATCH --tasks=10                           
#SBATCH --time=01:00:00                       # Time limit for each task


source /home/dimitri.imfeld/nas_home/AdGA/.venv/bin/activate

whoami

# Run the Python script with the task ID
mpirun -np 10 /home/dimitri.imfeld/nas_home/AdGA/.venv/bin/python3 mpi_test.py > out.txt
