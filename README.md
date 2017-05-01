# Log Parser

The program runs a daemon which processes log



### Prerequisites

Python 2.6+ required.
The logs being written should be of format
$ip_address\t$method $route\t$status_code\t$response_bytes


### Installing

```
git clone https://github.com/tgupta3/log_parser (Private Repo)
```


### Usage

```
$ python main.py start|stop|restart log_file
```
Synopsis:
```
$ python main.py action log_file [options]

  Options:
  -h, --help  			print help message and exit
  -l, --log-level		sets log level, choices={DEBUG,INFO,WARNING,ERROR,CRITICAL}
  -d, --daemon-log		sets the output log file for daemon
  -f, --pid-file		sets the pidfile for daemon
  -o, --output-file		sets the output file for daemon
```
Defaults:
```
Default log-level is info
Default daemon-log are stored in /tmp/daemon.log
Default output-file is stored in /tmp/daemon_output.txt
Default pid file is stored in /tmp/daemon_pid.pid
```
The logs can be genrated by running 
```
$ python webserver.py -o access.log -r 5

  Options:
  -o,		Output file for log
  -r,		Rotation interval, default is 30sec
```



