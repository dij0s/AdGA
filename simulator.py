import time
import threading
from rallyrobopilot import *
from collections import deque
from math import sqrt

class Simulator:
    """
    Simulate a series of controls
    on a car instance
    """
    def __init__(self, controls, init_position, init_speed, init_rotation, simulation_queue, ursina_callback):
        # TODO: Add init_speed
        super().__init__()

        self._controls = deque(controls)
        self._init_position = init_position
        self._init_speed = init_speed
        self._init_rotation = init_rotation
        self.simulation_queue = simulation_queue
        self._recorded_data = []
        self._ursina_callback = ursina_callback

        # setup backend
        self._setup_server()

    def start(self):
        # Run a loop in a thread on a timed interval to check for end of simulation
        self.running = True
        self.loop_thread = threading.Thread(target=self._sim_loop)
        self.loop_thread.start()

        self.car.reset_position = self._init_position
        self.car.reset_orientation = (0, self._init_rotation, 0)
        self.car.reset_speed = self._init_speed 
        self.car.reset_car()

        print(f"[LOG] Resetted car properties: position: {self.car.position}, rotation: {self.car.rotation}, speed: {self.car.speed}")

        self.running = True

    def _sim_loop(self):
        while self.running:
            time.sleep(1//120)  

            if self.car.simulation_done:
                print("[LOG] Simulation done")
                self.running = False
                print(f"[LOG] Received a total of {len(self.car.recorded_data)} sensor messages")
                self.simulation_queue.put(self.car.recorded_data)
                print("Am I killing ?")
                self._ursina_callback()
                print("Killed..")

    def _setup_server(self):
        # Setup track and car
        track = Track("rallyrobopilot/assets/SimpleTrack/track_metadata.json")

        car = Car(position=self._init_position, speed=self._init_speed, rotation=(0, self._init_rotation, 0))
        car.sports_car()
        car.set_track(track)
        car.controls_queue = self._controls
        car.simulate_controls = True
        self.car = car

        self.controller = RemoteController(car=car)

        car.visible = True
        car.enable()

        track.activate()
        track.played = True

        print("[LOG] Backend entities are all setup")
