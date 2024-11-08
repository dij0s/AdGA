from PyQt6.QtCore import QTimer
from PyQt6 import QtWidgets

import sys

from flask import Flask
from threading import Thread

from collections import deque
from rallyrobopilot import *

class Simulator(QtWidgets.QMainWindow):
    """
    Simulate a series of controls
    on a car instance through
    the network
    """
    def __init__(self, controls, init_position):
        # TODO: Add init_speed
        super().__init__()

        self._controls = deque(controls)
        self._init_position = init_position
        self._recorded_data = []

        # setup backend
        self._setup_server();

    def start(self):
        print("[LOG] Waiting for backend setup..")

        # wait for backend setup
        self.initial_timer = QTimer()
        self.initial_timer.setSingleShot(True)
        self.initial_timer.timeout.connect(self._start_network_interface)
        self.initial_timer.start(10000)
        
        # TODO: RETURN DATA AT THE END

    def get_recorded_data(self):
        return self._recorded_data

    def _start_network_interface(self):
        print("[LOG] Starting network interface")

        # create network interface
        self.network_interface = NetworkDataCmdInterface(self._collect_data)

        print("[LOG] Created network interface")

        # connect to socket
        self.timer = QTimer()
        self.timer.timeout.connect(self.network_interface.recv_msg)
        self.timer.start(25)

    def _setup_server(self):
        # setup track and car
        global_models = [ "sports-car.obj", "particles.obj",  "line.obj"]
        global_texs = [ "sports-red.png", "sports-blue.png", "sports-green.png", "sports-orange.png", "sports-white.png", "particle_forest_track.png", "red.png"]

        track = Track("rallyrobopilot/assets/SimpleTrack/track_metadata.json")
        track.load_assets(global_models, global_texs)

        car = Car(position = self._init_position)
        car.sports_car()
        car.set_track(track)

        car.multiray_sensor = MultiRaySensor(car, 15, 90)
        car.multiray_sensor.enable()

        RemoteController(car=car, connection_port=7654)
        
        car.visible = True
        car.enable()

        track.activate()
        track.played = True

        print("[LOG] Backend entities are all setup")

    def _collect_data(self, message):
        self._recorded_data.append(message)
        
        current_control = self._controls.popleft()
        print(current_control)
        # TODO: HANDLE IF THERE IS NONE LEFT
        for index, (command, start) in enumerate(current_control):
            print(index, command)
            self._send_command(command, start)

    def _send_command(self, direction, start):
        command_types = ["release", "push"]
        self.network_interface.send_cmd(command_types[start] + " " + direction+";")