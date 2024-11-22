

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
    def __init__(self, model_dill_filepath):
        # load model
        with open(model_dill_filepath, "rb") as file:
            self.model = dill.load(file)

    def nn_infer(self, message):
        return self.model.predict(message)

    def process_message(self, message, data_collector):
        commands = self.nn_infer(message)

        for command, start in commands:
            data_collector.onCarControlled(command, start)

if  __name__ == "__main__":
    import sys
    import dill
    # !
    import pickle
    import lzma
    import dill

    from pathlib import Path

    from functools import reduce

    import numpy as np

    import torch
    from torch import nn
    import torch.optim as optim
    import torch.nn.functional as F

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook

    app = QtWidgets.QApplication(sys.argv)

    nn_brain = OsdNNMsgProcessor(sys.argv[1])
    data_window = DataCollectionUI(nn_brain.process_message)
    data_window.show()

    app.exec()