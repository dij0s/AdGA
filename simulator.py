import time
import threading
from rallyrobopilot import *
from math import sqrt

class Simulator:
    """
    Simulate a series of controls
    on a car instance through
    the network
    """
    def __init__(self, controls, init_position, init_speed, init_rotation, simulation_queue, ursina_callback):
        # TODO: Add init_speed
        super().__init__()

        self._controls = controls
        self._init_position = init_position
        self._init_speed = init_speed
        self._init_rotation = init_rotation
        self._simulation_queue = simulation_queue
        self._recorded_data = []
        self._ursina_callback = ursina_callback

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
        print("[LOG] Loaded track metadata")

        car = Car(position=self._init_position, speed=self._init_speed, rotation=(0, self._init_rotation, 0))
        car.sports_car()
        car.set_track(track)

        controller = RemoteController(car=car, connection_port=7654)
        print(f"[LOG] Created remote controller (listening socket: {controller.listen_socket})")

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
            self._simulation_queue.put(self._recorded_data)
            self._ursina_callback()

    def _send_command(self, direction, start):
        command_types = ["release", "push"]
        self.network_interface.send_cmd(command_types[start] + " " + direction + ";")
