
import socket
import time

class SimpleCollector:
    def __init__(self):
        self.data = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("127.0.0.1", 7654))

    def run(self):
        """
        while True:
            self.listen_socket.recv(1024)
            self.listen_socket.send(b"coucou")

            time.sleep(0.1)
        """
        pass


if __name__ == "__main__":
    collector = SimpleCollector()
    collector.run()
    time.sleep(1)
    collector.socket.send(b'push forward;')
    time.sleep(2)
    collector.socket.send(b'release forward;')
    time.sleep(1)
    collector.socket.send(b'push forward;push right;')
    time.sleep(1)
    collector.socket.send(b'release forward;release right;')