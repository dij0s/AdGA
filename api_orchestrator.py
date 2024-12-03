import threading
from flask import Flask, jsonify, request
import json
import time

import requests

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_requests_session(retries=20, backoff_factor=0.3):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["POST"],
        backoff_factor=backoff_factor
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

class ApiOrchestratorSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, max_simultaneous_requests=10):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize(max_simultaneous_requests)
        return cls._instance

    def _initialize(self, max_simultaneous_requests):
        self.max_simultaneous_requests = max_simultaneous_requests
        self.pods_usage = {}
        self.pods = []
        self.session = create_requests_session()
        
        try:
            with open('sim-pods.json', 'r') as f:
                pods_info = json.load(f)
            self.pods = pods_info['items']
            for pod in self.pods:
                self.pods_usage[pod['status']['podIP']] = 0
            print(f"Found {len(self.pods)} pods")
        except Exception as e:
            print(f"Error loading pods: {e}")
            self.pods = []

    def get_least_used_pod(self):
        if not self.pods:
            raise ValueError("No pods available")
        
        min_usage = min(self.pods_usage.values())
        candidates = [k for k, v in self.pods_usage.items() if v == min_usage]
        return min(candidates)  # Deterministic selection if multiple pods have same usage

app = Flask(__name__)
class ApiOrchestratorApi:
    @app.route('/api/route', methods=['POST'])
    def route():
        try:
            data = request.get_json()
            orchestrator = ApiOrchestratorSingleton()
            
            with orchestrator.lock:
                min_pod = orchestrator.get_least_used_pod()
                orchestrator.pods_usage[min_pod] += 1
            
            start_time = time.time()
            try:
                response = orchestrator.session.post(
                    f"http://{min_pod}:5000/api/simulate", 
                    json=data, 
                    timeout=(5, 30)  # (connect timeout, read timeout)
                )
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Request failed to {min_pod}: {e}")
                return jsonify({
                    "error": "Failed to communicate with the simulator", 
                    "exception": str(e)
                }), 500
            finally:
                with orchestrator.lock:
                    orchestrator.pods_usage[min_pod] -= 1
            
            print(f"Request to {min_pod} took {time.time() - start_time:.2f} seconds")
            return jsonify(response.json()), response.status_code
        
        except Exception as e:
            print(f"Unexpected error in routing: {e}")
            return jsonify({"error": "Internal orchestration error"}), 500