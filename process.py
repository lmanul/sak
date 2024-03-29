"Describes a UNIX process"

class Process:
    "Describes a UNIX process"
    def __init__(self, data):
        self.user = data[0]
        self.pid = data[1]
        self.percent_cpu = data[2]
        self.percent_mem = data[3]
        self.vsz = data[4]
        self.rss = data[5]
        self.tty = data[6]
        self.stat = data[7]
        self.start = data[8]
        self.time = data[9]
        self.cmd = data[10]
        if len(data) > 11:
            self.args = " ".join(data[11:])

    def __str__(self):
        return "<Process cmd=" + self.cmd + ">"

    @staticmethod
    def parse_ps_aux_line(line):
        "Returns a Process parsed from a line taken from 'ps aux' output"
        parts = list(filter(lambda x: (x.strip() != ""), line.split(" ")))
        return Process(parts)

    def matches_binary(self, binary_name):
        "Returns whether this process is running a binary with this name"
        if self.cmd == binary_name:
            return True
        if self.cmd.endswith("/" + binary_name):
            return True
        return False
