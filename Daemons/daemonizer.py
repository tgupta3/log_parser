#!usr/bin/env python
"""
This module implement a standard daemon
The daemon class is reponsible for performing all the daemon related function before
it can actually become a daemon
"""

import sys
import os
import time
import atexit
import logging
import errno
from signal import SIGTERM

class Daemon(object):
    """
    General Daemon class supports start,stop,restart
    """
    def __init__(self, pidfile, stdout, stdin='/dev/null', stderr='/dev/null'):

        """
        Constructor
        """

        self.stdout = stdout
        self.stdin = stdin
        self.stderr = stderr
        self.pidfile = pidfile
        logger = logging.getLogger("Daemon.__init__")
        logger.debug("Daemon Constructor created")

    def create_daemon(self):
        """
        Daemon Intialize
        """

        logger = logging.getLogger("Daemon.createDaemon")

        try:
            pid = os.fork()
            if pid > 0:
                logger.info("Created First PID=%d", pid)
                sys.exit(0)
        except OSError as err:
            logger.error("First fork failed: %s", err)
            sys.exit(1)

        try:
            os.umask(0)  # Change the file mode mask
            os.setsid()  # Create a new session id
            os.chdir("/")  # change directory to root
        except OSError as err:
            logger.error("Error in umask|setsid|chdir: %s", err)

        # Forking twice and exit immediately to prevent zombies
        try:
            pid = os.fork()
            if pid > 0:
                logger.info("Main PID=%d", pid)
                sys.exit(0)
        except OSError as err:

            logger.error("Error in second fork:%s", err)
            sys.exit(1)

        # Redirect out the standard file descriptor
        pid = str(os.getpid())
        sys.stdout.write("PID is %s\n" % pid)
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'w+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        #Write Pidfile,delete on exit
        atexit.register(self.delpid)

        file(self.pidfile, 'w+').write("%s\n" % pid)

        logger.info("Daemon Created")

    def start(self):
        """
        Method to check if daemon is already running.
        If not, it will create the daemon and run it
        """
        logger = logging.getLogger("Daemon.start")
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().rstrip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            sys.stdout.write("Pidfile %s found. Daemon already running?\n" % self.pidfile)
            logger.error("Pidfile %s found. Daemon already running with pid=%s", self.pidfile, pid)
            sys.exit(1)

        self.create_daemon()
        self.run()

    def delpid(self):
        """
        Delete the pid file
        if daemon exits unexpextedely
        """
        logger = logging.getLogger("Daemon.delpid")
        logger.critical("PID File deleted.Daemon didn't start")
        os.remove(self.pidfile)

    def run(self):
        """
        Run method
        """
        pass

    def stop(self):
        """
        Stop the daemon
        """
        logger = logging.getLogger('Daemon.stop')
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().rstrip())
            pf.close()
        except IOError as err:
            logging.debug("PID file Error %s", err)
            pid = None

        if not pid:

            sys.stdout.write("Pidfile %s not found. Daemon not running\n" % self.pidfile)
            logger.error("Pidfile %s not found. Daemon not running", self.pidfile)
            return

        # Try killing the daemon process
        try:
            while True:
                os.kill(pid, SIGTERM)
                time.sleep(0.5)
        except OSError as err:
            if err.errno == errno.ESRCH:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                else:
                    logger.error("Error in removing: %s", err)
                    sys.exit(1)

        logger.info("Daemon Stopped")

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()
