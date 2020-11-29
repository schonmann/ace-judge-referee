import sys

class StreamWrapper(object):
    def __init__(self, *argv):
        self.streams = argv
    def write(self, message):
        for stream in self.streams:
            stream.write(message)
    def flush(self):
        pass

def redirect_stdout_to(stream):
    def decorator(func):
        def func_wrapper():
            sys.stdout = StreamWrapper(sys.__stdout__, stream)
            func()
            sys.stdout = sys.__stdout__
        return func_wrapper
    return decorator