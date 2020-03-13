import subprocess
import time
from . import verdict as v
from subprocess import PIPE, Popen
import signal

class CommandTimeout(Exception):
    pass

def alarm_handler(signum, frame):
    raise CommandTimeout

def run_command_timeout(command, input, timeout=3):
    p = Popen(command, stdout=PIPE, stdin=PIPE)

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)

    p.stdin.write(input)

    try:
        stdoutdata, stderrdata = p.communicate()
        signal.alarm(0)
        return stdoutdata, stderrdata
    except CommandTimeout:
        pass

def verdict(executable_path, input, expected_output, compile_error = False):

    if compile_error:
        return {
            'runtime': 0.000,
            'verdict': v.COMPILE_ERROR
        }

    start_time = time.time()

    stdout, stderr = run_command_timeout([executable_path], input, 3)

    runtime = time.time() - start_time

    return {
        'runtime': runtime,
        'verdict': get_verdict(runtime, stdout, stderr, expected_output),
    }

def get_verdict(runtime, stdout, stderr, expected_output):
    if stderr : # runtime error
        return v.RUNTIME_ERROR
    if runtime > 3.0: # time limit
        return v.TIME_LIMIT_EXCEEDED
    if expected_output != stdout:
        return v.WRONG_ANSWER # presentation error maybe?
    return v.CORRECT_ANSWER