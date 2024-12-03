import time
import requests
from flask import Flask, jsonify, request
from multiprocessing import Process, Queue
from simulator import Simulator
from ursina import *
import time
import uuid

app = Flask(__name__)
app_id = str(uuid.uuid4()) 

# Define a queue to communicate with the simulation process
simulation_queue = Queue()


def run_simulation(fake_controls, init_pos, init_speed, init_rotation, simulation_queue):
    try:
        # Run Ursina and PyQt within this process
        from ursina import Ursina


        # Initialize the Ursina and PyQt applications
        ursina_app = Ursina(size=(320, 256))
        kill_ursina = lambda: ursina_app.destroy()

        # Start the simulator
        simulation = Simulator(fake_controls, init_pos, init_speed, init_rotation, simulation_queue, kill_ursina)
        simulation.start()

        # Run Ursina event loop
        ursina_app.run()
    except Exception as e:
        print("[PROCESS ERROR] /api/simulate/ - Failed to run the simulation")
        print(e)
        exit(1)

@app.route('/api/simulate', methods=['POST'])
def simulate():
    print(f"[/api/simulate/] Received request to simulate @{app_id}")
    # try:
    #     requests.get("http://192.168.89.26:8080")
    # except Exception as e:
    #     print("[ERROR] /api/simulate/ - Failed to communicate with the logger")
    #     print(e)
    #     return jsonify({"error": "Failed to communicate with the logger", "exception": e}), 500

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

        # Check if the process died and exited with an error
        if not process.is_alive() and process.exitcode != 0:
            print(f"[/api/simulate/] ERROR - Simulation process has exited unexpectedly (crashed or something) @{app_id}")
            return jsonify({"error": "Simulation process has exited unexpectedly (crashed or something)"}), 500

    simulation_data = simulation_queue.get()
    process.kill()

    print(f"[/api/simulate/] Simulation completed successfully @{app_id}")
    print(f"[/api/simulate/] Returning simulation data: \n ===>{simulation_data}")
    return jsonify(simulation_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
