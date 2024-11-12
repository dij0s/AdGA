import time
import threading
from rallyrobopilot import *
from collections import deque
from math import sqrt

class Simulator:
    """
    Simulate a series of controls
    on a car instance through
    the network
    """
    def __init__(self, controls, init_position, init_speed, simulation_queue):
        # TODO: Add init_speed
        super().__init__()

        self._controls = deque(controls)
        self._init_position = init_position
        self._init_speed = init_speed
        self.simulation_queue = simulation_queue
        self._recorded_data = []

        # setup backend
        self._setup_server()

    def start(self):
        print("[LOG] Waiting for backend setup...")

        # Wait for backend setup with a delay (5 seconds)
        timer_thread = threading.Timer(5.0, self._start_network_interface)
        timer_thread.start()

    def _start_network_interface(self):
        print("[LOG] Starting network interface")

        # Create network interface
        self.network_interface = NetworkDataCmdInterface(self._collect_data)
        print("[LOG] Created network interface")

        # Simulate network message sending on a timed interval
        self.running = True
        self.network_thread = threading.Thread(target=self._network_loop)
        self.network_thread.start()

        print("[LOG] Configured network interface")

    def _network_loop(self):
        while self.running:
            self.network_interface.send_msg()
            time.sleep(0.1)  # 100 ms delay

    def _setup_server(self):
        # Setup track and car
        track = Track("rallyrobopilot/assets/SimpleTrack/track_metadata.json")

        car = Car(position=self._init_position, speed=self._init_speed)
        car.sports_car()
        car.set_track(track)

        RemoteController(car=car, connection_port=7654)
        
        car.visible = True
        car.enable()

        track.activate()
        track.played = True

        print("[LOG] Backend entities are all setup")

    def _collect_data(self, message):
        self._recorded_data.append(message)
        
        if self._controls:
            current_control = self._controls.popleft()
            for command, start in current_control:
                self._send_command(command, start)
        else:
            print("[LOG] No controls left")
            self._recorded_data = [sensor.car_position for sensor in self._recorded_data[1:]]
            print(f"[LOG] Received a total of {len(self._recorded_data)} sensor messages")

            # Stop the network loop and clean up
            self.running = False
            self.network_interface.close()
            self.simulation_queue.put(self._recorded_data)

    def _send_command(self, direction, start):
        command_types = ["release", "push"]
        self.network_interface.send_cmd(command_types[start] + " " + direction + ";")

    def _compute_fitness(self):
        # Compute fitness of current trajectory
        # Fitness is the distance travelled by the car
        total_vector_magnitude = 0.0
        for p1, p2 in zip(self._recorded_data[:-1], self._recorded_data[1:]):
            x1, z1, y1 = p1
            x2, z2, y2 = p2

            dx = x2 - x1
            dz = z2 - z1
            dy = y2 - y1
            
            total_vector_magnitude += sqrt(dx**2 + dy**2 + dz**2)

        return total_vector_magnitude
