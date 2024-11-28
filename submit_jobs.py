import subprocess

from optimize_trajectory import GAManager


REQUESTS_PER_POD = 3
NODELIST = "calypso[1]"
N_NODES = 1
N_TASKS_PER_NODE = 24
N_TASKS = N_NODES * N_TASKS_PER_NODE
SPLIT_WINDOW_SIZE = 10
SPLIT_OVERLAP = 5


result = subprocess.run("kubectl get pods --no-headers -n isc3 |  awk '{print $1}'  | uniq -c | wc -l", stdout=subprocess.PIPE, shell=True, text=True)
pods_count = int(result.stdout.strip())

genetic_algorithm = GAManager()
trajectories = genetic_algorithm.split_recording_into_trajectories(
    "records/record_241119111936.npz",
    split_window_size=SPLIT_WINDOW_SIZE,
    split_overlap=SPLIT_OVERLAP
)

n_trajectories = len(trajectories)
max_concurrent_requests = (pods_count * REQUESTS_PER_POD) // n_trajectories

template_file = "submit_jobs.template"
template_content = open(template_file).read()
template_content = template_content.replace("%%MAX_CONCURRENT_REQUESTS%%", str(max_concurrent_requests))
template_content = template_content.replace("%%N_TASKS%%", str(N_TASKS))
template_content = template_content.replace("%%N_TASKS_PER_NODE%%", str(N_TASKS_PER_NODE))
template_content = template_content.replace("%%N_NODES%%", str(N_NODES))
template_content = template_content.replace("%%NODELIST%%", NODELIST)

with open("submit_jobs.sh", "w") as f:
    f.write(template_content)

subprocess.Popen("sbatch submit_jobs.sh", start_new_session=True, shell=True)
