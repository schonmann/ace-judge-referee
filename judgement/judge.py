import subprocess
import time
from . import verdict as v
from subprocess import PIPE, Popen
import signal
from utils.command import run_command_timeout, CommandTimeout

def verdict(executable_path, input, expected_output, compile_error = False):
    time_limit=20
    if compile_error:
        return {
            'runtime': 0.000,
            'verdict': v.COMPILE_ERROR
        }
    try:
        start_time = time.time()
        stdout, stderr = run_command_timeout(executable_path, input, time_limit)
        runtime = time.time() - start_time
        return {
            'runtime': runtime,
            'verdict': get_verdict(stdout, stderr, expected_output),
        }
    except CommandTimeout:
        return {
            'runtime': 1 + time_limit * 1000, # ms
            'verdict': v.TIME_LIMIT_EXCEEDED,
        }
    except:
        return {
            'runtime': None,
            'verdict': v.GENERIC_ERROR
        }
        

def get_verdict(stdout, stderr, expected_output):
    if stderr : # runtime error
        return v.RUNTIME_ERROR
    if expected_output.strip() != stdout.strip():
        print(expected_output)
        print(stdout)
        return v.WRONG_ANSWER # presentation error maybe?
    return v.CORRECT_ANSWER