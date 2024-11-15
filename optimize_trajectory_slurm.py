import sys
import time
import numpy as np
from optimize_trajectory import GAManager

def main(task_id):
    genetic_algorithm = GAManager(population_size=10)

    # Split the recording into trajectories
    trajectories = genetic_algorithm.split_recording_into_trajectories("records/record_241106093055.npz")

    # Ensure the task_id is within the range of trajectories
    if task_id >= len(trajectories):
        raise ValueError(f"Task ID {task_id} is out of range for the number of trajectories {len(trajectories)}")

    trajectory = trajectories[task_id]
    initial_state = {
        "init_pos": trajectory[1][0],
        "init_speed": trajectory[2][0],
        "init_rotation": trajectory[3][0],
    }

    pop = genetic_algorithm.create_population(trajectory[0], trajectory[1], n=10, p=0.2)

    evolved_pop, fitnesses = genetic_algorithm.evolve(pop, 10, initial_state)

    z = zip(evolved_pop, fitnesses)
    best = sorted(z, key=lambda x: x[1], reverse=True)[0]
    print(best)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python optimize_trajectory_slurm.py <task_id>")
        sys.exit(1)

    task_id = int(sys.argv[1])
    main(task_id)