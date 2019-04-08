import subprocess
import time
from . import verdict as v
from subprocess import PIPE, Popen


def run_command_timeout(command, timeout):
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    for t in xrange(timeout):
        time.sleep(1)
        if p.poll() is not None:
            return p.communicate()
    p.kill()
    return False

def verdict(executable_path, input, expected_output, compile_error = False):

    if compile_error:
        return {
            'runtime': 0.000,
            'verdict': v.COMPILE_ERROR
        }

    start_time = time.time()

    program_output = run_command_timeout([executable_path, '<<<', '"{0}"'.format(input)], 3)

    runtime = time.time() - start_time
    
    return {
        'runtime': runtime,
        'verdict': get_verdict(runtime, program_output, expected_output),
    }

def get_verdict(runtime, program_output, expected_output):
    if runtime > 3.0: # time limit
        return v.TIME_LIMIT_EXCEEDED
    if program_output != 0: # runtime error
        return v.RUNTIME_ERROR
    if expected_output != program_output:
        return v.WRONG_ANSWER # presentation error maybe?
    return v.CORRECT_ANSWER