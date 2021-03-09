import signal
from subprocess import PIPE, Popen
import celeryconfig as config
import shlex
import os

class CommandTimeout(Exception):
    pass

def alarm_handler(signum, frame):
    raise CommandTimeout

def run_command_timeout(command, input, timeout=3, stdout=PIPE, stdin=PIPE):
    try:
        sandbox_command = "{}/scripts/bubblewrap.sh {}".format(config.root_path, command)
        p = Popen(shlex.split(sandbox_command), stdout=stdout, stdin=stdin)

        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(timeout)

        p.stdin.write(input)
        
        stdoutdata, stderrdata = p.communicate()
        signal.alarm(0)
        return stdoutdata, stderrdata
    except CommandTimeout:
        pass
