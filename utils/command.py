import signal
from subprocess import PIPE, Popen

class CommandTimeout(Exception):
    pass

def alarm_handler(signum, frame):
    raise CommandTimeout

def run_command_timeout(command, input, timeout=3, stdout=PIPE, stdin=PIPE):
    p = Popen(command, stdout=stdout, stdin=stdin)

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)

    p.stdin.write(input)

    try:
        stdoutdata, stderrdata = p.communicate()
        signal.alarm(0)
        return stdoutdata, stderrdata
    except CommandTimeout:
        pass
