
import socket
import time
import imageio

from sensing_message import *

class SimpleCollector:
    def __init__(self):
        self.data = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("127.0.0.1", 7654))
        self.socket.setblocking(False)

        self.msg_mngr = SensingMessageManager(self.process_sensing_message)

    def recv_msg(self):
        try:
            while True:
                data = self.socket.recv(2**20)

                if len(data) == 0:
                    break

                self.msg_mngr.add_message_chunk(data)

        except Exception as e:
            print(e)
            pass

    def process_sensing_message(self, sensing_snapshot):
        print("sensing_snapshot.car.position =", sensing_snapshot.car_position)

        imageio.imsave("last_image.png", sensing_snapshot.image)



if __name__ == "__main__":
    collector = SimpleCollector()

    time.sleep(2)
    collector.socket.send(b'set ray hidden;')
    x = 0
    while x < 10:
        collector.recv_msg()
        x += 1
        time.sleep(0.5)

    """
    time.sleep(1)
    collector.socket.send(b'push forward;')
    time.sleep(2)
    collector.socket.send(b'release forward;')
    time.sleep(1)
    collector.socket.send(b'push forward;push right;')
    time.sleep(1)
    collector.socket.send(b'release forward;release right;')
    time.sleep(1)
    collector.socket.send(b'reset;')
    time.sleep(1)
    collector.socket.send(b'set rotation 90;')
    collector.socket.send(b'reset;')
    time.sleep(1)
    collector.socket.send(b'set rotation 180;')
    collector.socket.send(b'reset;')
    time.sleep(1)
    collector.socket.send(b'set rotation 270;')
    collector.socket.send(b'reset;')
    """