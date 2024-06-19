import curses
import os
import re
import shlex
import shutil
import signal
import subprocess
import time

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def sanitize_string(s):
    return ANSI_ESCAPE.sub('',
        str(s.encode('utf-8').decode('ascii', 'ignore')).replace("\x00", ''))

class Status:
    STOPPED = 0
    PREPARING = 1
    READY = 2

class Mode:
    ROWS = 0
    COLUMNS = 1

class MultiRunnerProcess:
    "If no 'ready pattern' is passed, we assume instant readiness"
    def __init__(self, command, name, working_dir, ready_pattern=None,
            spam_filter=None, tokens_to_filter_out=[]):
        self.command = command
        self.name = name
        self.working_dir = working_dir
        self.inner_process = None
        self.ready_pattern = ready_pattern
        self.spam_filter = spam_filter
        self.tokens_to_filter_out = tokens_to_filter_out
        self.status = Status.PREPARING
        self.output = []

    def start(self):
        app_env = {}
        self.inner_process = subprocess.Popen(
            shlex.split(self.command),
            cwd=self.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        # Make reading from stdout/stderr non-blocking
        os.set_blocking(self.inner_process.stdout.fileno(), False)
        os.set_blocking(self.inner_process.stderr.fileno(), False)

    def should_log_line(self, l):
        if l == "":
            return False
        if self.spam_filter and self.spam_filter(l):
            return False
        return True

    def process_log_line(self, l):
        l = l.strip()
        # Collapse white space
        l = ' '.join(l.split())
        if len(self.tokens_to_filter_out) > 0:
            for token in self.tokens_to_filter_out:
                l = l.replace(token, "")
        return l

    def ingest_log_buffer(self, stream):
        text = sanitize_string(stream.read1().decode())
        lines = [self.process_log_line(l) for l in text.split("\n")]
        lines = [l for l in lines if self.should_log_line(l)]
        self.output += lines
        if self.status == Status.PREPARING:
            for line in lines:
                if not self.ready_pattern or self.ready_pattern in line:
                    self.status = Status.READY

    def update_io(self):
        try:
            if self.inner_process.stdout:
                self.ingest_log_buffer(self.inner_process.stdout)
            if self.inner_process.stderr:
                self.ingest_log_buffer(self.inner_process.stderr)
            if not self.is_alive():
                self.status = Status.STOPPED
        except UnicodeDecodeError:
            pass

    def print_raw_logs(self):
        for stream in [self.inner_process.stdout, self.inner_process.stderr]:
            text = stream.read1().decode().strip()
            if text != "":
                print(text)

    def is_alive(self):
        return self.inner_process.poll() is None

    def quit(self):
        print("Quitting '" + self.name + "' (" + str(self.inner_process.pid) + ") ...")
        tries = 0
        while self.is_alive():
            if tries < 3:
                print("Sending interrupt signal to '" + self.name + "'...")
                self.inner_process.send_signal(signal.SIGINT)
            elif tries < 6:
                print("Sending kill signal to '" + self.name + "'...")
                self.inner_process.send_signal(signal.SIGKILL)
            else:
                print("Sending 'kill -9' to '" + self.name + "'...")
                os.system("kill -9 " + str(self.inner_process.pid))
            self.print_raw_logs()
            tries += 1
            time.sleep(2)
        print(self.name + " has ended.")

class MultiRunner:
    def __init__(self):
        self.processes = []
        self.screen = None
        self.running = True
        self.mode = Mode.ROWS
        self.width = 0
        self.height = 0
        self.inner_height = 0
        # Remember the total log size of what we displayed last, to avoid
        # flickering when there is nothing new.
        self.last_output_size = 0
        self.force_next_refresh = False

    def update_dimensions(self):
        self.height, self.width = self.screen.getmaxyx()
        self.inner_height = self.height - 1 # Minus status bar

    def total_output_size(self):
        total = 0
        for process in self.processes:
            total += len(process.output)
        return total

    def add(self, command, name, working_dir=None, ready_pattern=None,
            spam_filter=None, tokens_to_filter_out=[]):
        self.processes.append(MultiRunnerProcess(command, name, working_dir,
            ready_pattern, spam_filter, tokens_to_filter_out))

    def on_input(self, key):
        if key == ord("q"):
            self.running = False
        elif key == ord("h"):
            self.mode = Mode.ROWS
            self.force_next_refresh = True
        elif key == ord("v"):
            self.mode = Mode.COLUMNS
            self.force_next_refresh = True
        elif key == curses.KEY_RESIZE:
            self.force_next_refresh = True

    def quit(self):
        for process in self.processes:
            process.quit()

    def draw_title(self, screen, index):
        n_processes = len(self.processes)
        width = self.width if self.mode == Mode.ROWS else \
            int(self.width / n_processes)
        row = 0 if self.mode == Mode.COLUMNS else int(index * self.inner_height / n_processes)
        col = 0 if self.mode == Mode.ROWS else int(index * self.width / n_processes)
        process = self.processes[index]
        icon = ["🛑", "🚧", "✅"][process.status]
        title = process.name + " " + icon
        separator = " " * int((width - len(title) - 2) / 2)
        color = 1 + index % 4
        screen.attron(curses.color_pair(color))
        screen.addstr(row, col, separator + " " + title + " " + separator)
        screen.attroff(curses.color_pair(color))

    def draw_status_bar(self, screen):
        statusbarstr = "q — Exit    h — Horiz.    v — Vertic."
        screen.attron(curses.color_pair(5))
        screen.addstr(self.height - 1, 0, statusbarstr)
        screen.addstr(self.height - 1, len(statusbarstr),
            " " * (self.width - len(statusbarstr) - 1))
        screen.attroff(curses.color_pair(5))

    def draw_one_process(self, screen, index):
        n_processes = len(self.processes)
        process = self.processes[index]
        one_process_width = self.width
        first_col = 0
        last_row = 0
        first_row = 1
        if self.mode == Mode.ROWS:
            # +1 for the title
            first_row = 1 + int(index * self.inner_height / n_processes)
            one_process_height = int((self.inner_height - (n_processes - 1)) / n_processes)
            last_row = first_row + one_process_height - 1
        elif self.mode == Mode.COLUMNS:
            first_col = int(index * self.width / n_processes)
            one_process_width = int((self.width - (n_processes - 1)) / n_processes)
            last_row = self.inner_height - 1
        row = last_row
        row_from_bottom = 0
        while row >= first_row:
            if len(process.output) > row_from_bottom:
                screen.addstr(row, first_col,
                    process.output[-row_from_bottom - 1][0:one_process_width - 1])
            row_from_bottom += 1
            row -= 1
        if self.mode == Mode.COLUMNS and index < n_processes - 1:
            # Draw a separator column
            row = last_row
            while row >= first_row:
                screen.addstr(row, first_col + one_process_width, "|")
                row -= 1

    def refresh(self):
        total_output_size = self.total_output_size()
        if not self.force_next_refresh and total_output_size == self.last_output_size:
            return
        # Something new happened
        self.last_output_size = total_output_size
        row = 0
        self.screen.clear()
        for i in range(len(self.processes)):
            self.draw_title(self.screen, i)
            self.draw_one_process(self.screen, i)
        self.draw_status_bar(self.screen)
        self.screen.refresh()
        self.force_next_refresh = False

    def draw(self, screen):
        self.init(screen)
        while self.running:
            key = screen.getch()
            for process in self.processes:
                process.update_io()
            self.on_input(key)
            self.update_dimensions()
            self.refresh()
            time.sleep(0.3)

    def init(self, screen):
        self.screen = screen
        self.screen.nodelay(1)
        # screen.noecho()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def start(self):
        for process in self.processes:
            process.start()
        curses.wrapper(self.draw)
        self.quit()
