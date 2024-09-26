
from sensing_message import *

from PyQt6.QtCore import Qt, QTimer
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6 import uic

class DataCollectionUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("DataCollector.ui", self)

        buttons = [self.forwardButton, self.backwardButton, self.rightButton, self.leftButton]
        self.command_directions = { "w":"forward", "s":"back", "d":"right", "a":"left" }

        self.forwardButton.pressed.connect(lambda : self.onCarControlled("forward", True))
        self.forwardButton.released.connect(lambda : self.onCarControlled("forward", False))

        self.backwardButton.pressed.connect(lambda : self.onCarControlled("back", True))
        self.backwardButton.released.connect(lambda : self.onCarControlled("back", False))

        self.rightButton.pressed.connect(lambda : self.onCarControlled("right", True))
        self.rightButton.released.connect(lambda : self.onCarControlled("right", False))

        self.leftButton.pressed.connect(lambda : self.onCarControlled("left", True))
        self.leftButton.released.connect(lambda : self.onCarControlled("left", False))

        self.recordDataButton.clicked.connect(self.toggle_record)
        self.resetButton.clicked.connect(self.resetNForget)

        self.network_interface = NetworkDataCmdInterface(self.collectMsg)

        self.timer = QTimer()
        self.timer.timeout.connect(self.network_interface.recv_msg)
        self.timer.start(25)

        self.recording = False

        self.recorded_data = []
    def collectMsg(self, msg):
        if self.recording:
            self.recorded_data.append(msg)

            if not self.saveImgCheckBox:
                msg.image = None
    def resetNForget(self):

        if self.recording:
            nbr_snapshots_to_forget = self.forgetSnapshotNumber.value() if len(self.recorded_data) > self.forgetSnapshotNumber.value() else len(self.recorded_data)-1

            self.recorded_data = self.recorded_data[:-nbr_snapshots_to_forget]

            self.network_interface.send_cmd("set position "+ str(self.recorded_data[-1].car_position)[1:-1].replace(" ","")+";")
            self.network_interface.send_cmd("set rotation "+ str(self.recorded_data[-1].car_angle)+";")
            self.network_interface.send_cmd("reset;")

            self.toggle_record()

    def toggle_record(self):
        self.recording = not self.recording
        self.recordDataButton.setText("Recording..." if self.recording else "Record")

    def onCarControlled(self,direction, start):
        command_types = ["release", "push"]
        self.network_interface.send_cmd(command_types[start] + " " + direction+";")

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        if isinstance(event, QtGui.QKeyEvent):
            key_text = event.text()
            print(key_text)
            if key_text in self.command_directions:
                self.onCarControlled(self.command_directions[key_text], True)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if isinstance(event, QtGui.QKeyEvent):
            key_text = event.text()
            if key_text in self.command_directions:
                self.onCarControlled(self.command_directions[key_text], False)

if __name__ == "__main__":

    import sys
    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook

    app = QtWidgets.QApplication(sys.argv)

    data_window = DataCollectionUI()
    data_window.show()

    app.exec()


        ###############################

    """
    collector = DataCollectionUI()

    time.sleep(1)
    #   After a second instruct the car to start moving forward
    collector.socket.send(b'push forward;')

    #   Collect sensing snapshot for 5 seconds
    x = 0
    while x < 8:
        collector.recv_msg()
        x += 1
        time.sleep(0.5)

    #   After 4 seconds -> instruct car to stop and reset
    collector.socket.send(b'release forward;reset;')
    """