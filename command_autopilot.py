

from PyQt6 import QtWidgets

from data_collector import DataCollectionUI
"""
This file is provided as an example of what a simplistic controller could be done.
It simply uses the DataCollectionUI interface zo receive sensing_messages and send controls.

/!\ Be warned that if the processing time of NNMsgProcessor.process_message is superior to the message reception period, a lag between the images processed and commands sent.
One might want to only process the last sensing_message received, etc. 
Be warned that this could also cause crash on the client side if socket sending buffer overflows

/!\ Do not work directly in this file (make a copy and rename it) to prevent future pull from erasing what you write here.
"""
class OsdNNMsgProcessor:
    def __init__(self, ga_inputs):
        # load commands into queue
        raw_inputs = np.load(ga_inputs)['arr_0'].copy().reshape(-1, 8)
        
        # only take n-overlap first
        # commands to not handle overlap
        self._commands = deque([map(lambda x: int(x), raw_input[1:5]) for raw_input in raw_inputs])
        
        self._directions = ["forward", "back", "left", "right"]

    def process_message(self, _, data_collector):
        current_command = self._commands.popleft()
        for command, start in map(lambda ic: (self._directions[ic[0]], ic[1]), enumerate(current_command)):
            data_collector.onCarControlled(command, start)

if  __name__ == "__main__":
    import sys

    import numpy as np
    from collections import deque

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook

    app = QtWidgets.QApplication(sys.argv)

    nn_brain = OsdNNMsgProcessor(sys.argv[1])
    data_window = DataCollectionUI(nn_brain.process_message)
    data_window.show()

    app.exec()