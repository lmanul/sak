class Monitor:
    "Represents a monitor, with id, orientation, resolution"
    def __init__(self, input_id, rotation="normal", scale=1, resolution=None,
                 primary=False, connected=True):
        self.input_id = input_id
        self.rotation = rotation
        self.scale = scale
        self.resolution = resolution
        self.primary = primary
        self.connected = connected

    def __str__(self):
        return "'" + self.input_id + " -- " + ("" if self.connected else "dis") + "connected"

