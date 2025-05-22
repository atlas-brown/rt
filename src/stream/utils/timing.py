import logging
import time

class Timing:
    message = None
    logf = None
    start = None

    # message: str or (number -> str)
    # if it's a string, it will be appended with the time as a string
    # if it's a function, it will be called with the time to construct a message
    def __init__(self, message, logf=logging.debug):
        self.message = message
        self.logf = logf

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exn_type, exn_value, exn_tb):
        elapsed_secs = time.time() - self.start
        if isinstance(self.message, str):
            self.logf(self.message + str(elapsed_secs))
        else:
            self.logf(self.message(elapsed_secs))
        return False
