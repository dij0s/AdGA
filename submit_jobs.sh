#!/bin/bash
#SBATCH --job-name=ga_optimization
#SBATCH --output=ga_optimization_%A_%a.out
#SBATCH --error=ga_optimization_%A_%a.err
#SBATCH --nodelist=calypso[3]             
#SBATCH --nodes=1                             
#SBATCH --tasks=36                          

source ~/.venv/bin/activate

# Run the Python script with the task ID
mpirun -np 36  python optimize_trajectory_slurm.py
