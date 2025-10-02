import logging
import os
import logging.handlers # <-- FIX: Import the handlers submodule

LOG_FILE = 'trading_bot_log.log'

def setup_logging():
    """Configures centralized logging for the application."""
    log_format = (
        '%(asctime)s | %(levelname)-8s | '
        '%(module)s:%(funcName)s:%(lineno)d | %(message)s'
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    # 2. File Handler (for the required log files)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024 * 5, # 5 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))

    # 3. Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Lowest level for file logging

    # Prevent adding duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")

    # Return the file name for the application task submission
    return LOG_FILE

if __name__ == '__main__':
    setup_logging()
    logging.info("This is an info log.")