#!/usr/bin/env python

"""
This script produces a log file similar to what you'd see from a web server.
"""
from collections import defaultdict
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


def generate_log_line(output_map):
    """Generate a random log line."""
    ip=get_random_ip(),
    method=random.choice(METHODS),
    route=random.choice(ROUTES),
    status_code=random.choice(STATUS_CODES),
    response_bytes=random.randint(64, RESPONSE_BYTES_MAX)
    output_map[str(route[0])+'\t'+str(status_code[0])]+=1
    
    
    return LOG_FORMAT.format(
        ip=ip[0],
        method=method[0],
        route=route[0],
        status_code=status_code[0],response_bytes=response_bytes
    )


class Logger(object):
    def __init__(self, log_filename, rotate_secs):
        self.log_filename = log_filename
        self.rotate_secs = rotate_secs

        self.log_file = Logger.open(log_filename)
        self.last_rotate = time.time()

    @staticmethod
    def open(log_filename):
        return open(log_filename, "w", 1)

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
        last_track=0
        output_map=defaultdict(lambda:0)
        filename='/home/tgupta/dropbox/completed.txt'
        while True:
            if self.should_rotate():
                
                self.rotate_logfile()
            
            with open(filename) as f_obj:
                lines=f_obj.readlines()

            
            if int(lines[0].rstrip())-last_track>0:
                last_track=int(lines[0].rstrip())
                print "\n"
                for output in output_map.keys():
                    print ("%s\t%s"%(output,str(float(output_map[output])/10)))
                
                print "total\t%s"%(sum(output_map.itervalues()))
                output_map=defaultdict(lambda:0)
                
                

            self.log_file.write(generate_log_line(output_map))
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
        type=float, default=30.0,
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