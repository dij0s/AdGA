#!/bin/bash
#SBATCH --job-name=ga_optimization
#SBATCH --output=ga_optimization_%A_%a.out
#SBATCH --error=ga_optimization_%A_%a.err
#SBATCH --nodelist=calypso[0]             # Use only these 3 nodes
#SBATCH --nodes=1                             # Use 3 nodes (each node will run some jobs)
#SBATCH --tasks=10                           # 56 tasks, one per array job (task array size)
#SBATCH --time=01:00:00                       # Time limit for each task


source /home/dimitri.imfeld/nas_home/AdGA/.venv/bin/activate

# Run the Python script with the task ID
mpirun -np 10 /home/dimitri.imfeld/nas_home/AdGA/.venv/bin/python3 optimize_trajectory_slurm.py
