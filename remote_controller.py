
from ursina import *
import socket
import numpy as np

from sensing_message import SensingSnapshot, SensingSnapshotManager
from remote_commands import RemoteCommandParser

REMOTE_CONTROLLER_VERBOSE = False
PERIOD_REMOTE_SENSING = 0.1

def printv(str):
    if REMOTE_CONTROLLER_VERBOSE:
        print(str)

class RemoteController(Entity):
    def __init__(self, car = None, connection_port = 7654):
        super().__init__()

        self.ip_address = "127.0.0.1"
        self.port = connection_port
        self.car = car

        self.listen_socket = None
        self.connected_client = None

        self.client_commands = RemoteCommandParser()

        self.reset_location = (0,0,0)
        self.reset_speed = (0,0,0)
        self.reset_rotation = 0

        #   Period for recording --> 0.1 secods = 10 times a second
        self.sensing_period = PERIOD_REMOTE_SENSING
        self.last_sensing = -1

    def update(self):
        self.update_network()
        self.process_remote_commands()
        self.process_sensing()

    def process_sensing(self):
        if self.car is None or self.connected_client is None:
            return

        if time.time() - self.last_sensing >= self.sensing_period:
            snapshot = SensingSnapshot()
            snapshot.current_controls = (held_keys['w'], held_keys['s'], held_keys['a'], held_keys['d'])
            snapshot.car_position = self.car.world_position
            snapshot.car_speed = self.car.speed
            snapshot.car_angle = self.car.rotation_y
            snapshot.raycast_distances = self.car.multiray_sensor.collect_sensor_values()

            #   Collect last rendered image
            tex = base.win.getDisplayRegion(0).getScreenshot()
            arr = tex.getRamImageAs("RGB")
            data = np.frombuffer(arr, np.uint8)
            image = data.reshape(tex.getYSize(), tex.getXSize(), 3)
            image = image[::-1, :, :]#   Image arrives with inverted Y axis

            snapshot.image = image

            msg_mngr = SensingSnapshotManager()
            data = msg_mngr.pack(snapshot)

            try:
                self.connected_client.sendall(data)
            except ConnectionError as e:
                self.connected_client.close()
                self.connected_client = None

            self.last_sensing = time.time()

    def process_remote_commands(self):
        if self.car is None:
            return

        while len(self.client_commands) > 0:
            try:
                commands = self.client_commands.parse_next_command()
                print("Processing command", commands)
                if commands[0] == b'push' or commands[0] == b'release':
                    if commands[1] == b'forward':
                        held_keys['w'] = commands[0] == b'push'
                    elif commands[1] == b'back':
                        held_keys['s'] = commands[0] == b'push'
                    elif commands[1] == b'right':
                        held_keys['d'] = commands[0] == b'push'
                    elif commands[1] == b'left':
                        held_keys['a'] = commands[0] == b'push'


                elif commands[0] == b'set':
                    if commands[1] == b'position':
                        self.car.reset_position = commands[2]
                    elif commands[1] == b'rotation':
                        self.car.reset_orientation = (0, commands[2], 0)
                    elif commands[1] == b'speed':
                        # Todo
                        pass
                    elif commands[1] == b'ray':
                        self.car.multiray_sensor.set_enabled_rays(commands[2] == b'visible')

                elif commands[0] == b'reset':
                    self.car.reset_car()

            #   Error is thrown when commands do not fit the model --> disconnect client
            except Exception as e:
                print("Invalid command --> disconnecting : " + str(e))
                self.connected_client.close()
                self.connected_client = None

    def update_network(self):
        if self.connected_client is not None:
            data = []
            try:
                while True:
                    recv_data = self.connected_client.recv(1024)

                    #received nothing
                    if len(recv_data) == 0:
                        break
                    self.client_commands.add(recv_data)

            except Exception as e:
                printv(e)

        #   No controller connected
        else:
            if self.listen_socket is None:
                self.open_connection_socket()
            try:
                inc_client, address = self.listen_socket.accept()
                print("Controller connecting from " + str(address))
                self.connected_client = inc_client
                self.connected_client.setblocking(False)

                #   Close listen socket
                self.listen_socket.close()
                self.listen_socket = None
            except Exception as e:
                printv(e)


    def open_connection_socket(self):
        print("Waiting for connections")
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.ip_address, self.port))
        self.listen_socket.setblocking(False)
        self.listen_socket.listen()

if __name__ == "__main__":
    app = Ursina()
    window.title = "Rally"
    window.borderless = False
    remote_controller = RemoteController()
    app.run()