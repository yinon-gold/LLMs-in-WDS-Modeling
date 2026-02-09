import logging
import os
from datetime import datetime

def setup_logger():
    """
    Set up and configure the logger for the llm_epanet project.
    Returns a configured logger instance.
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger('llm_epanet')
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if not logger.handlers:
        log_file = os.path.join(logs_dir, f'llm_epanet_{datetime.now().strftime("%Y_%m_%d_%H-%M-%S")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s::%(funcName)s() line %(lineno)d | %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger() 