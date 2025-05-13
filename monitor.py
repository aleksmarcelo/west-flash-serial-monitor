import os
import sys
import subprocess
import socket
import threading
import signal
import time
import argparse
import textwrap
import importlib.util

'''west "monitor" command'''

from west.commands import WestCommand

from run_common import add_parser_common, do_run_common, get_build_dir

from pathlib import Path

# Global variables
# ANSI escape codes for colors and styles (global constants)
INVERSE = "\033[7m"
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
BOLD = "\033[1m"
YELLOW = "\033[93m"

# Port for listening to commands
COMMAND_PORT = 5555

def check_picocom_installed():
    if subprocess.call(["which", "picocom"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        print(f"{RED}Error: picocom is not installed. Please install it:{RESET}")
        print(f"  sudo apt install picocom\n")
        sys.exit(1)

def start_serial_monitor(args):
    global monitor_process, last_command_was_pause
    try:
        monitor_process = subprocess.Popen(
            # ["picocom"] + args,
            ["picocom", "--quiet"] + args,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )

        monitor_process.wait()

    finally:
        # Always restore the terminal after picocom exit
        restore_terminal()

    # If picocom exited and last command was not pause, exit monitor.py, it measn contro a + control x
    if not last_command_was_pause:
        print(f"\r{INVERSE}{YELLOW}Shutting down picocom...{RESET}")
        os._exit(0)
        
def terminate_picocom():
    global last_command_was_pause
    last_command_was_pause = True
    if monitor_process and monitor_process.poll() is None:
        try:
            monitor_process.terminate()
            
            # brief moment to clean up
            time.sleep(0.2)
            
            # If it's still running, force
            if monitor_process.poll() is None:
                monitor_process.kill()
                
            monitor_process.wait()
        except Exception:
            pass

def listen_for_commands(args):
    global monitor_process, last_command_was_pause
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", COMMAND_PORT))
        while True:
            data, _ = sock.recvfrom(1024)
            command = data.strip().lower()
            if command == b"pause":
                if monitor_process and monitor_process.poll() is None:
                    print(f"\r{INVERSE}{RED}serial monitor paused. Flashing in progress...{RESET}\n")
                    terminate_picocom()  # Terminate the picocom process
            elif command == b"continue":
                if not monitor_process or monitor_process.poll() is not None:
                    last_command_was_pause = False
                    threading.Thread(target=start_serial_monitor, args=(args,), daemon=True).start()
                    print(f"\r{INVERSE}{GREEN}{BOLD}picocom restarted{RESET}\n")


def restore_terminal():
    try:
        sys.stdout.flush()
        subprocess.run(["stty", "sane"], check=False)
        # subprocess.run(["reset"], check=False)
    except Exception:
        pass

def start_monitor(args):
    
    # if ommited, 115200 will be baudrate and loof for /dev/ttyUSB?
    if len(args)==0:
        if "-b" not in args:
            args.extend(["-b", "115200"])
        if not any(arg.startswith("/dev/tty") for arg in args):
            usb_devices = [dev for dev in os.listdir('/dev') if dev.startswith('ttyUSB')]
            if usb_devices:
                args.append(f"/dev/{usb_devices[0]}")
            else:
                args.append("/dev/ttyUSB?")

    print(f"args: {' '.join(args)}")
    check_picocom_installed()

    # Ignore SIGTERM to prevent monitor.py from exiting when picocom is terminated
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    global last_command_was_pause
    last_command_was_pause = False

    listener_thread = threading.Thread(target=listen_for_commands, args=(args,), daemon=True)
    listener_thread.start()

    threading.Thread(target=start_serial_monitor, args=(args,), daemon=True).start()

    # Wait for the listener thread to finish
    while True:
        signal.pause()


class Monitor(WestCommand):

    def __init__(self):
        super().__init__(
            'monitor',
            # Keep this in sync with the string in west-commands.yml.
            'open a serial monitor (only on linux, depends on picocom)',
            "open a serial monitor (only on linux, depends on picocom)",
            accepts_unknown_args=True)

    def do_add_parser(self, parser_adder):
        default_fmt = '{name}'
        parser = parser_adder.add_parser(
            self.name,
            help=self.help,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="Open a serial monitor using picocom (Linux only).",
            epilog=textwrap.dedent(f'''\
            USAGE
            -----
            This command opens a serial monitor using picocom. It is only
            supported on Linux and requires picocom to be installed.

            All possible picocom options can be used here. To see the available
            options, run `picocom --help`.

            To exit the monitor, press `Ctrl+A` followed by `Ctrl+X` (as the same in picocom!-).
            '''))

        # flags
        parser.add_argument('-b', '--baud', type=int, default=115200,
                            help='Baud rate for the serial connection (default: 115200)')
        parser.add_argument('-d', '--device', default=None,
                            help='Serial device to connect to (e.g., /dev/ttyUSB0)')
        return parser

    def do_run(self, my_args, runner_args):
        start_monitor(runner_args)

