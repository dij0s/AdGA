import struct

import numpy as np


def iter_unpack(format, data):
    nbr_bytes = struct.calcsize(format)
    return struct.unpack(format, data[:nbr_bytes]), data[nbr_bytes:]

class SensingSnapshot:
    def __int__(self):
        self.car_position = (0,0,0)
        self.car_speed = 0
        self.raycast_distances = [0]
        self.image = None

    def pack(self):
        byte_data = b''
        byte_data += struct.pack(">ffff", self.car_position[0], self.car_position[1], self.car_position[2], self.car_speed)

        nbr_raycasts = len(self.raycast_distances)
        byte_data += struct.pack(">B" + "f" * nbr_raycasts, nbr_raycasts, *self.raycast_distances)

        if self.image is not None:
            byte_data += struct.pack(">ii", self.image.shape[0], self.image.shape[1])
            byte_data +=  self.image.tobytes()
        else:
            byte_data += struct.pack(">ii", 0, 0)

        return byte_data

    def unpack(self, data):
        (x,y,z,s), data = iter_unpack(">ffff", data)
        self.car_position = (x,y,z)
        self.car_speed = s

        nbr_raycasts, data = iter_unpack(">B", data)
        self.raycast_distances, data = iter_unpack(">" + "f" * nbr_raycasts, data)

        h,w = iter_unpack(">ii", data)

        if h*w > 0:
            self.image = np.frombuffer(data, np.uint8).reshape(h,w,3)
        else:
            self.image = None


class SensingDataUnpacker:
    def __init__(self):
        self.pending_data = b''

    def add_data(self, data):
        self.pending_data += data
