import sys
import time
from flask import Flask, jsonify, request
from multiprocessing import Process, Queue
from simulator import Simulator
import json
import os
from ursina import application
import time

app = Flask(__name__)

# Define a queue to communicate with the simulation process
simulation_queue = Queue()

def run_simulation(fake_controls, init_pos, init_speed, simulation_queue):
    # Run Ursina and PyQt within this process
    from ursina import Ursina

    # Initialize the Ursina and PyQt applications
    ursina_app = Ursina(size=(320, 256))

    # Start the simulator
    simulation = Simulator(fake_controls, init_pos, init_speed, simulation_queue)
    simulation.start()

    # Run Ursina event loop
    ursina_app.run()

@app.route('/api/simulate', methods=['POST'])
def simulate():
    print("[LOG] Received request to simulate")
    data = request.get_json()

    fake_controls = data['controls']
    init_pos = data['init_pos']
    init_speed = data['init_speed']

    # Start the simulation process
    process = Process(target=run_simulation, args=(fake_controls, init_pos, init_speed, simulation_queue))
    process.start()
    
    # wait for something to be in the simulation queue
    while simulation_queue.empty():
        time.sleep(1)

    simulation_data = simulation_queue.get()
    process.kill()

    return jsonify(simulation_data)

if __name__ == '__main__':
    app.run(port=5000, debug=True)