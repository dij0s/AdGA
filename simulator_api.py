import time
import requests
from flask import Flask, jsonify, request
from multiprocessing import Process, Queue
from simulator import Simulator
from ursina import *
import time

app = Flask(__name__)

# Define a queue to communicate with the simulation process
simulation_queue = Queue()

def run_simulation(fake_controls, init_pos, init_speed, init_rotation, simulation_queue):
    # Run Ursina and PyQt within this process
    from ursina import Ursina

    # Initialize the Ursina and PyQt applications
    ursina_app = Ursina(size=(320, 256))

    # Start the simulator
    simulation = Simulator(fake_controls, init_pos, init_speed, init_rotation, simulation_queue)
    simulation.start()

    # Run Ursina event loop
    ursina_app.run()

@app.route('/api/simulate', methods=['POST'])
def simulate():
    print("[LOG] Received request to simulate")
    try:
        requests.get("http://192.168.89.26:8080")
    except e:
        return jsonify({"error": "Failed to communicate with the logger", "exception": e}), 500
        
    data = request.get_json()

    controls = data['controls']
    init_pos = data['init_pos']
    init_speed = data['init_speed']
    init_rotation = data['init_rotation']

    # Start the simulation process
    process = Process(target=run_simulation, args=(controls, init_pos, init_speed, init_rotation, simulation_queue))
    process.start()
    
    # Wait for something to be in the simulation queue
    while simulation_queue.empty():
        time.sleep(1)

        # Check if the process is still alive - if not, respond with an error
        if not process.is_alive():
            return jsonify({"error": "Simulation process has exited unexpectedly (crashed or something)"}), 500

    simulation_data = simulation_queue.get()
    process.kill()

    return jsonify(simulation_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)