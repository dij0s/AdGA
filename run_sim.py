from ursina import *
import sys

from simulator import Simulator

ursina_app = Ursina(size=(320,256))

fake_controls = [[("forward", 1), ("left", 1)], [("forward", 1), ("right", 1)], [("forward", 1)], [("forward", 1)], [("forward", 1)], [("forward", 1)], [("forward", 1)], [("forward", 1)], [("forward", 1)], [("forward", 1)]]

simulation = Simulator(fake_controls, (0, 0, 4), 10)
simulation.start()

ursina_app.run()