import subprocess
import time
from . import verdict as v
from subprocess import PIPE, Popen
import signal
from utils.command import run_command_timeout

def verdict(executable_path, input, expected_output, compile_error = False):

    time_limit=3
    if compile_error:
        return {
            'runtime': 0.000,
            'verdict': v.COMPILE_ERROR
        }

    start_time = time.time()
    stdout, stderr = run_command_timeout(executable_path, input, time_limit)
    runtime = time.time() - start_time

    return {
        'runtime': runtime,
        'verdict': get_verdict(runtime, stdout, stderr, expected_output, time_limit),
    }

def get_verdict(runtime, stdout, stderr, expected_output, time_limit):
    if stderr : # runtime error
        return v.RUNTIME_ERROR
    if runtime > time_limit: # time limit
        return v.TIME_LIMIT_EXCEEDED
    if expected_output.strip() != stdout.strip():
        print(expected_output)
        print(stdout)
        return v.WRONG_ANSWER # presentation error maybe?
    return v.CORRECT_ANSWER