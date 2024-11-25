#!/bin/bash
#SBATCH --job-name=ga_optimization
#SBATCH --output=logs/ga_optimization_%A.out
#SBATCH --error=logs/ga_optimization_%A.err
#SBATCH --nodelist=calypso[0]             
#SBATCH --nodes=1                             
#SBATCH --tasks=36                          

source ~/.venv/bin/activate

# Run the Python script with the task ID
mpirun -np 36  python optimize_trajectory_slurm.py
