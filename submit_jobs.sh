#!/bin/bash
#SBATCH --job-name=ga_optimization
#SBATCH --output=ga_optimization_%A_%a.out
#SBATCH --error=ga_optimization_%A_%a.err
#SBATCH --nodelist=calypso[0,2]             # Use only these 3 nodes
#SBATCH --nodes=2                             # Use 3 nodes (each node will run some jobs)
#SBATCH --tasks=36                          


source ~/.venv/bin/activate

# Run the Python script with the task ID
mpirun -np 60  ~/.venv/bin/python3 optimize_trajectory_slurm.py
