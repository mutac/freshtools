import logging
import sys

LOGGER_NAME = 'freshtools'

def get_logger():
    return logging.getLogger(LOGGER_NAME)


def log_to_stdout(level=logging.INFO):
    if level == logging.DEBUG:
        debug_formatter = logging.Formatter('[%(asctime)s]: %(message)s')
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(debug_formatter)
    else:
        info_formatter = logging.Formatter('%(message)s')
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(info_formatter)
    
    logger = logging.getLogger(LOGGER_NAME)
    logger.addHandler(stream)
    logger.setLevel(level)

    return logger