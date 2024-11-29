import subprocess

from optimize_trajectory import GAManager

CALYPSO_CPUS = {
    0: 48,
    1: 72,
}

# Parameters
calpsos_to_use = [ 1 ]
requests_per_pod = 2
split_window_size = 10
split_overlap = 5
trajectories_file = "records/record_241119111936.npz"
population_size = 10
elite_size = 2
mutation_rate = 0.1
iterations = 5

nodelist = f"calypso[{','.join([str(cpu) for cpu in calpsos_to_use])}]"
n_nodes = len(calpsos_to_use)
n_tasks = sum([CALYPSO_CPUS[calypso] for calypso in calpsos_to_use])
result = subprocess.run("kubectl get pods --no-headers -n isc3 |  awk '{print $1}'  | uniq -c | wc -l", stdout=subprocess.PIPE, shell=True, text=True)
pods_count = int(result.stdout.strip())

genetic_algorithm = GAManager()
trajectories = genetic_algorithm.split_recording_into_trajectories(
    trajectories_file,
    split_window_size=split_window_size,
    split_overlap=split_overlap
)

n_trajectories = len(trajectories)
max_concurrent_requests = (pods_count * requests_per_pod) // n_tasks

template_file = "submit_jobs.template"
template_content = open(template_file).read()

# no need to run more tasks than there are trajectories
if n_trajectories < n_tasks:
    n_tasks = n_trajectories

if n_trajectories > n_tasks:
    print("/!\ Warning: more trajectories than tasks! Some trajectories will not be processed.")


replacements = {
    "%%MAX_CONCURRENT_REQUESTS%%": str(max_concurrent_requests),
    "%%N_TASKS%%": str(n_tasks),
    "%%N_NODES%%": str(n_nodes),
    "%%NODELIST%%": nodelist,
    "%%TRAJECTORIES_FILE%%": trajectories_file,
    "%%POPULATION_SIZE%%": str(population_size),
    "%%ELITE_SIZE%%": str(elite_size),
    "%%MUTATION_RATE%%": str(mutation_rate),
    "%%ITERATIONS%%": str(iterations),
    "%%SPLIT_WINDOW_SIZE%%": str(split_window_size),
    "%%SPLIT_OVERLAP%%": str(split_overlap),
}

for key, value in replacements.items():
    template_content = template_content.replace(key, value)


with open("submit_jobs.sh", "w") as f:
    f.write(template_content)

subprocess.Popen("sbatch submit_jobs.sh", start_new_session=True, shell=True)
