#!/usr/bin/env python

"""
This script produces a log file similar to what you'd see from a web server.
"""

import argparse
import os
import random
import socket
import struct
import sys
import time


# Format used for randomly generated log lines.
LOG_FORMAT = "{ip}\t{method} {route}\t{status_code}\t{response_bytes}\n"

# Used to determine upper bound for a randomly generated
# response size.
RESPONSE_BYTES_MAX = 1024


def build_weighted_list(items):
    """
    Build a weighted list from a list of (item, weight) tuples.

    This is just a simple, albeit crude, wrapper to make weighted random easier.
    """
    new_list = []
    for item, weight in items:
        new_list.extend([item] * weight)
    return new_list


# List of methods and how often then should occur in log output
METHODS = build_weighted_list([
    ("GET", 95), ("POST", 5)
])

# List of status codes and how often then should occur in log output
STATUS_CODES = build_weighted_list([
    (200, 90), (404, 5), (500, 1)
])

# List of routes and how often then should occur in log output
ROUTES = build_weighted_list([
    ("/", 50), ("/library", 20), ("/blog", 20), ("/questions", 5)
])


def get_random_ip():
    """Generate a random IP address."""
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))


def generate_log_line():
    """Generate a random log line."""
    return LOG_FORMAT.format(
        ip=get_random_ip(),
        method=random.choice(METHODS),
        route=random.choice(ROUTES),
        status_code=random.choice(STATUS_CODES),
        response_bytes=random.randint(64, RESPONSE_BYTES_MAX)
    )


class Logger(object):
    def __init__(self, log_filename, rotate_secs):
        self.log_filename = log_filename
        self.rotate_secs = rotate_secs

        self.log_file = Logger.open(log_filename)
        self.last_rotate = time.time()

    @staticmethod
    def open(log_filename):
        return open(log_filename, "a", 1)

    def __del__(self):
        self.log_file.close()

    def should_rotate(self):
        return (time.time() - self.last_rotate) > self.rotate_secs

    def rotate_logfile(self):
        now = time.time()
        os.rename(self.log_filename, "{}.{}".format(self.log_filename, now))
        self.log_file.close()
        self.log_file = Logger.open(self.log_filename)
        self.last_rotate = now

    def log_forever(self):
        while True:
            if self.should_rotate():
                self.rotate_logfile()
            self.log_file.write(generate_log_line())
            sleep_for = random.randint(1, 10) / 100.0
            time.sleep(sleep_for)


def main(argv):
    parser = argparse.ArgumentParser(
        description="Web server log producer"
    )
    parser.add_argument(
        "--output-file", "-o", dest="output_file", metavar='FILE',
        type=str, required=True,
        help=(
            "the file where requests are logged. If this file "
            "already exists we will append to the file"
        )
    )
    parser.add_argument(
        "--log-rotation-interval", "-r", dest="lr_interval", metavar='SECONDS',
        type=int, default=30,
        help="How often to rotate out the file we're logging to in seconds."
    )
    args = parser.parse_args(argv[1:])

    logger = Logger(args.output_file, args.lr_interval)
    logger.log_forever()


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        sys.exit()
