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
#SBATCH --array=0-{num_trajectories - 1}
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --mem=4G

# Run the Python script with the task ID
/usr/bin/python3 optimize_trajectory_slurm.py ${{SLURM_ARRAY_TASK_ID}}
"""

    print(slurm_script)

    # Write the Slurm job script to a file
    with open("submit_jobs.sh", "w") as f:
        f.write(slurm_script)

    # Submit the Slurm job script
    subprocess.run(["sbatch", "submit_jobs.sh"])

if __name__ == "__main__":
    main()