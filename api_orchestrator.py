import threading
from flask import Flask, jsonify, request
import requests
import subprocess
import json

app = Flask(__name__)

class ApiOrchestratorSingleton:
    instance = None

    def init(max_simultaneous_requests):
        if ApiOrchestratorSingleton.instance is None:
            ApiOrchestratorSingleton.instance = ApiOrchestratorSingleton(max_simultaneous_requests)

    def __init__(self, max_simultaneous_requests):
        self.max_simultaneous_requests = max_simultaneous_requests
        self.pods_usage = {}
        self.pods = []

        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "isc3", "-l", "app=sim", "-o", "json"],
            capture_output=True,
            text=True
        )
        pods_info = json.loads(result.stdout)
        self.pods = pods_info['items']

        for i in self.pods:
            self.pods_usage[i['status']['podIP']] = 0

        self.lock = threading.Lock()

class ApiOrchestratorApi:
    @app.route('/api/route', methods=['POST'])
    def route():
        ApiOrchestratorSingleton.init(10)

        data = request.get_json()
        orchestrator = ApiOrchestratorSingleton.instance

        with orchestrator.lock:
            min_usage = min(orchestrator.pods_usage.values())
            min_pod = [k for k, v in orchestrator.pods_usage.items() if v == min_usage][0]
            orchestrator.pods_usage[min_pod] += 1

        try:
            response = requests.post(f"{min_pod}:5000/api/simulate", json=data)
        except Exception as e:
            return jsonify({"error": "Failed to communicate with the simulator", "exception": str(e)}), 500
        finally:
            with orchestrator.lock:
                orchestrator.pods_usage[min_pod] -= 1

        return jsonify(response.json()), response.status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)