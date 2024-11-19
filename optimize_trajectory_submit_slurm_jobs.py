import subprocess
from optimize_trajectory import GAManager

def main():
    print("Hello")
    genetic_algorithm = GAManager(population_size=10)
    print("world")

    # Split the recording into trajectories
    trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241106093055.npz")
    num_trajectories = len(trajectories)

    print("Num traj ", num_trajectories)

    # Create the Slurm job script
    slurm_script = f"""#!/bin/bash
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
"""

    print(slurm_script)

    # Write the Slurm job script to a file
    with open("submit_jobs.sh", "w") as f:
        f.write(slurm_script)

    # Submit the Slurm job script
    subprocess.run(["sbatch", "submit_jobs.sh"])

if __name__ == "__main__":
    main()
