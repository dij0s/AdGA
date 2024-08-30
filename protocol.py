
"""
Command must be followed by a semi colon !

Remote control protocol
#   Car controls
'push|release forward|left|right|back;'

#   set reset parameters
'set position x,y,z;' x/y/z are english style floats (with dot for decimal separator)
'set speed x,y,z;' x/y/z are english style floats (with dot for decimal separator)
'set rotation a;' a is an angle in degreees
'reset;'

#   Data message
'r' <-- car reset
'd' <-- data frame coming
"""

def equals(p1):
    def inner_is(p2):
        return p1 == p2, p1
    return inner_is

def contains(*values):
    def inner_contains(value):
        return value in values, value
    return inner_contains

def float_tuple(x):
    elems = x.split(b',')
    if len(elems) != 3:
        return False, (0,0,0)
    try:
        return True, tuple(float(e) for e in elems)
    except Exception as err:
        return False, (0,0,0)

def is_float(x):
    try:
        return True, float(x)
    except Exception as err:
        return False, 0.


class RemoteControlCommand:
    def __init__(self, *params):
        self.params = params

    def parse(self, command_words):
        parsed_command = []
        if len(self.params) > len(command_words):
            return None

        for pid, param in enumerate(self.params):
            checked, value = param(command_words[pid])
            if not checked:
                return None
            parsed_command.append(value)

        return parsed_command

    def __str__(self):
        return "RemoteControlCommand:" + "/".join(str(e) for e in self.params)

remote_control_commands = [
    #   Car control
    RemoteControlCommand(contains(b'push', b'release'), contains(b'forward', b'left', b'right', b'back')),
    #   Reset
    RemoteControlCommand(equals(b'reset')),
    #   Reset parameters command
    RemoteControlCommand(equals(b'set'), contains(b"position", b"speed"), float_tuple),
    RemoteControlCommand(equals(b'set'), equals(b"rotation"), is_float)
]

class RemoteCommandParser:
    def __init__(self):
        self.pending_data = b''
        self.command_words = []

    def add(self, data):
        self.pending_data += data
        next_semicol = self.pending_data.find(b';')
        while next_semicol > 0:
            command_string = self.pending_data[:next_semicol]
            next_space = command_string.find(b' ')
            command_words = []
            while next_space > 0:
                command_words.append(command_string[:next_space])
                command_string = command_string[next_space+1:]
                next_space = command_string.find(b' ')
            command_words.append(command_string)

            self.command_words.append(command_words)
            print("Appending command words =", command_words)

            self.pending_data = self.pending_data[next_semicol+1:]
            next_semicol = self.pending_data.find(b';')

    def __len__(self):
        return len(self.command_words)

    def parse_next_command(self):
        if len(self.command_words) == 0:
            return None

        for command_pattern in remote_control_commands:
            command = command_pattern.parse(self.command_words[0])
            if command is not None:
                self.command_words = self.command_words[1:]
                return command

        raise Exception("Invalid command in stack: " + str(self.command_words[:5]))


if __name__ == "__main__":
    acc = RemoteCommandParser()
    acc.add(b'push forward;')
    acc.add(b'push left;')
    acc.add(b'push right;')
    acc.add(b'push back;')
    acc.add(b'release forward;')
    acc.add(b'release left;')
    acc.add(b'release right;')
    acc.add(b'release back;')
    acc.add(b'set position 1.34,12,43;')
    acc.add(b'set rotation 234;')
    acc.add(b'set speed 234,54.2,67.2;')
    acc.add(b'reset;')
    acc.add(b'faketest;')

    try:
        while True:
            print("command =", acc.parse_next_command())
    except Exception as e:
        print(e)