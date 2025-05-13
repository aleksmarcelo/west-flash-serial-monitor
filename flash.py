# Copyright (c) 2018 Open Source Foundries Limited.
# Copyright 2019 Foundries.io
# Copyright (c) 2020 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: Apache-2.0

'''west "flash" command'''

import time
from west.commands import WestCommand

from run_common import add_parser_common, do_run_common, get_build_dir

from pathlib import Path
import socket

# Define the UDP port for communication
COMMAND_PORT = 5555

# ANSI escape codes for colors and styles (global constants)
INVERSE = "\033[7m"
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
BOLD = "\033[1m"
YELLOW = "\033[93m"

# Function to send a command via UDP
def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(command.encode(), ("127.0.0.1", COMMAND_PORT))


class Flash(WestCommand):

    def __init__(self):
        super(Flash, self).__init__(
            'flash',
            # Keep this in sync with the string in west-commands.yml.
            'flash and run a binary on a board',
            "Permanently reprogram a board's flash with a new binary.",
            accepts_unknown_args=True)
        self.runner_key = 'flash-runner'  # in runners.yaml

    def do_add_parser(self, parser_adder):
        return add_parser_common(self, parser_adder)

    def do_run(self, my_args, runner_args):
        build_dir = get_build_dir(my_args)
        domains_file = Path(build_dir) / 'domains.yaml'

        # Pause the serial monitor before running the command
        try:
            send_command("pause")
            time.sleep(1)  
            print(f"{YELLOW}Serial monitor paused for flashing.{RESET}")
        except Exception as e:
            print(f"Warning: Failed to pause serial monitor: {e}")

        do_run_common(self, my_args, runner_args, domain_file=domains_file)

        # Restart the serial monitor after running the command
        try:
            send_command("continue")
            print(f"{YELLOW}Serial monitor restarted after flashing.{RESET}")
        except Exception as e:
            print(f"Warning: Failed to restart serial monitor: {e}")

