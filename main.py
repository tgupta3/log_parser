#!usr/bin/env python

"""
Daemon to process logs

Usage main.py (start|stop|restart) logfile_to_parse [options]

[options]
    --log-level=(debug|info|warning|error|criticall)
    --daemon-log=PATH #Log file for daemon
    --output-file=PATH #output file for daemon
    --pid-file=PATH #pidfile
Make sure pid-file is unique for every logfile_to_parse

"""

from collections import defaultdict
import logging
import re
import datetime
import os
import argparse
import sys
import time
from Daemons import Daemon


DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def valid_arg(file_name):
    """
    Checks if file_name entered has valid path.
    """

    if not os.path.isabs(file_name):
        return os.path.join(os.getcwd(), file_name)
    else:
        return file_name


class MyDaemon(Daemon):
    """
    inherits the Daemon class and overides the run method

    """

    def __init__(self, log_file, pidfile, stdout, interval=10):
        """
        Constructor
        """
        super(MyDaemon, self).__init__(pidfile, stdout)
        self.log_file = log_file
        self.interval = interval
        self.output_map = defaultdict(lambda: 0)
        self.today = datetime.date.today()

    def open(self, line_visited):
        """
        Returns node no of log file, and lines not visited
        """
        logger = logging.getLogger("MyDaemon.open")
        while True:
            try:
                with open(self.log_file, 'r') as file_obj:
                    node_curr = os.fstat(file_obj.fileno()).st_ino
                    return (
                        [line for line_no, line in enumerate(file_obj)
                         if line_no not in range(0, line_visited)],
                        node_curr
                    )
            except IOError as err:
                logger.debug("Log file opening error.Error:%s", err)
                continue

    def should_print(self, time_last_pass):
        """
        check output is printed every interval
        """
        return (time.time() - time_last_pass) > self.interval

    def display_output(self):
        """
        writes output to stdout in this format
        """

        day = DAYS[datetime.date.weekday(self.today)]
        output_format = '{:%b %d %H:%M:%S %Y}'.format(datetime.datetime.now())
        print "\n%s %s" % (day, output_format)
        print '=' * 40
        for output in self.output_map.keys():
            print ("%s\t%s" %
                   (output, str(float(self.output_map[output]) / 10)))
        print "total\t%s" % (sum(self.output_map.itervalues()))
        self.output_map = defaultdict(lambda: 0)

    @staticmethod
    def match_pattern(line):
        """
        Return matched line
        """
        return re.search("(/\w*)\t([0-9]+)\t([0-9]+)", line)

    def run(self):
        """
        Overiding the run method
        """
        logger = logging.getLogger("MyDaemon.run")
        logger.info("Daemon is running")
        node_curr = 0
        line_visited = 0
        #last_track = 0
        time_last_pass = time.time()

        while True:
            lines, node_next = self.open(line_visited)
            if node_next != node_curr:
                logger.debug(
                    "File was rotated,"
                    "Last inode was %s, Present is %s",
                    node_curr, node_next)
                node_curr = node_next
                line_visited = 0

            for line in lines:

                line_visited += 1
                match = MyDaemon.match_pattern(line)

                if match:
                    output_key = match.group(
                        1) + '\t' + match.group(2)
                    self.output_map[output_key] += 1
                else:
                    logger.warning(
                        "Possible error in the log-file being parsed")

            # Write to stdout every 10sec
            if self.should_print(time_last_pass):
                '''with open(
                    '/home/tgupta/dropbox/completed.txt', 'w', 1
                ) as comp:
                    comp.write(str(last_track + 1))
                    last_track += 1'''

                self.display_output()
                time_last_pass = time.time()


def main(argv):
    """
    Start here
    Main for Daemon to process logs
    """

    parser = argparse.ArgumentParser(
        description="Daemon to process logs"
    )
    parser.add_argument(
        "action", metavar="action_for_daemon", type=str,
        choices=['start', 'stop', 'restart'],
        help=(
            "Defines action for daemon."
            "Possible action= start|stop|restart"
        )
    )
    parser.add_argument(
        "log_file", metavar="Log_file_to_parse", type=valid_arg,
        help=(
            "Defines the log file to process"
        )
    )
    parser.add_argument(
        "-l", "--log-level", dest="logLevel",
        choices=['DEBUG', 'INFO', 'WARNING', "ERROR", 'CRITICAL'],
        default='INFO',
        help="Set the logging level,default=CRITICAL"
    )
    parser.add_argument(
        "-d", "--daemon-log", dest="daemonLog",
        type=valid_arg, default='/tmp/daemon.log',
        metavar='log file',
        help="Set the log file,default is /tmp/daemon.log"
    )
    parser.add_argument(
        "-o", "--output-file", dest="outFile",
        type=valid_arg, default='/tmp/daemon_output.txt',
        metavar='output File',
        help="Set the output file,default is /tmp/daemon_output.txt"
    )
    parser.add_argument(
        "-p", "--pid-file", dest="pidFile",
        type=valid_arg, default='/tmp/daemon_pid.pid',
        metavar='pid File',
        help="Set the pid file,default is /tmp/daemon_pid.pid"
    )

    args = parser.parse_args(argv[1:])

    logger = logging.getLogger("")
    logger.setLevel(getattr(logging, args.logLevel))
    logger.propagate = False
    filelog = logging.FileHandler(args.daemonLog, mode='a')
    formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
    filelog.setFormatter(formatter)
    logger.addHandler(filelog)
    logger.info("Logger is set to %s", args.logLevel)

    daemon = MyDaemon(args.log_file, args.pidFile, args.outFile)

    if args.action == 'start':
        logger.info("Starting daemon for Logfile=%s", args.log_file)
        daemon.start()

    if args.action == 'stop':
        logger.info("Stopping daemon for Logfile=%s", args.log_file)
        daemon.stop()

    if args.action == 'restart':
        logger.info("Restart daemon for Logfile=%s", args.log_file)
        daemon.restart()


if __name__ == "__main__":
    main(sys.argv)
