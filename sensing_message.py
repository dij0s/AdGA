import struct

import numpy as np


def iter_unpack(format, data):
    nbr_bytes = struct.calcsize(format)
    return struct.unpack(format, data[:nbr_bytes]), data[nbr_bytes:]

"""
    SensingSnapshot is a packing/unpacking class for diverse car simulation related information
"""
class SensingSnapshot:
    def __init__(self):
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

        (nbr_raycasts,), data = iter_unpack(">B", data)
        print(nbr_raycasts)
        self.raycast_distances, data = iter_unpack(">" + "f" * nbr_raycasts, data)

        (h,w), data = iter_unpack(">ii", data)

        if h*w > 0:
            self.image = np.frombuffer(data, np.uint8).reshape(h,w,3)
        else:
            self.image = None

"""
#   Snapshot formatting and managing class
#       --> pass it the chunks received via socket, the class correctly split and parse the received messages
#       uses a callback to inform higher level code of reception of a complete SensingSnapshot
"""
class SensingSnapshotManager:
    def __init__(self, received_snapshot_callback = None):
        self.pending_data = b''
        self.received_snapshot_callback = received_snapshot_callback

    def pack(self, snapshot):
        data = snapshot.pack()
        data = struct.pack(">i", len(data)) + data

        return data


    def add_message_chunk(self, chunk):
        self.pending_data += chunk

        sizeheader = struct.calcsize(">i")
        message_size = struct.unpack(">i", self.pending_data[:sizeheader])[0]

        print("expecting data size =", message_size, " <? ", len(self.pending_data))

        if message_size+sizeheader <= len(self.pending_data):
            print("Recv full message")
            snapshot = SensingSnapshot()

            snapshot.unpack(self.pending_data[sizeheader:sizeheader+message_size])
            print("self.received_msg_callback =", self.received_snapshot_callback)
            if self.received_snapshot_callback is not None:
                print("callbacking")
                self.received_snapshot_callback(snapshot)

            self.pending_data = self.pending_data[sizeheader+message_size:]