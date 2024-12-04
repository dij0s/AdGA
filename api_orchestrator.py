import threading
from flask import Flask, jsonify, request
import requests
import subprocess
import json
from requests.adapters import HTTPAdapter

from urllib3 import Retry

app = Flask(__name__)

def create_requests_session(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=backoff_factor
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

class ApiOrchestratorSingleton:
    instance = None

    def init(max_simultaneous_requests):
        if ApiOrchestratorSingleton.instance is None:
            ApiOrchestratorSingleton.instance = ApiOrchestratorSingleton(max_simultaneous_requests)

    def __init__(self, max_simultaneous_requests):
        self.max_simultaneous_requests = max_simultaneous_requests
        self.pods_usage = {}
        self.pods = []

        self.session = create_requests_session()

        with open('sim-pods.json', 'r') as f:
            pods_info = json.loads(f.read())
        self.pods = pods_info['items']

        for i in self.pods:
            self.pods_usage[i['status']['podIP']] = 0

        print(f"Found {len(self.pods)} pods")

        self.lock = threading.Lock()

class ApiOrchestratorApi:
    @app.route('/api/route', methods=['POST'])
    def route():
        ApiOrchestratorSingleton.init(10)

        data = request.get_json()
        orchestrator = ApiOrchestratorSingleton.instance

        print(f"Received request to simulate")
        print(data)

        with orchestrator.lock:
            min_usage = min(orchestrator.pods_usage.values())
            min_pod = [k for k, v in orchestrator.pods_usage.items() if v == min_usage][0]
            print(f"Selected pod {min_pod}")
            orchestrator.pods_usage[min_pod] += 1

        try:
            print(f"Sending request to {min_pod}")
            response = orchestrator.session.post(f"http://{min_pod}:5000/api/simulate", json=data)
        except Exception as e:
            print(f"Failed to communicate with the simulator")
            print(e)
            return jsonify({"error": "Failed to communicate with the simulator", "exception": str(e)}), 500
        finally:
            with orchestrator.lock:
                print(f"Releasing pod {min_pod}")
                orchestrator.pods_usage[min_pod] -= 1

        return jsonify(response.json()), response.status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
