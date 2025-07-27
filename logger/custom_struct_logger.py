import os
import logging
from datetime import datetime
import structlog

class CustomStructLogger:
    def __init__(self, log_dir="logs"):
        # Ensure all log files are stored in a dedicated 'logs' directory located alongside this script.
        self.logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_dir)
        
        # Create the logs directory if it doesn't exist
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Generate the log file name with timestamp
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        
        # Set the full path for the log file
        self.log_file_path = os.path.join(self.logs_dir, log_file)
        
    def get_logger(self, name=__file__) -> any:
        logger_name = os.path.basename(name)

        # Configure file logging. This will log raw JSON lines to the file
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(message)s"))  # Raw JSON lines

        # Configure console logging. This will log raw JSON lines to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",  # Structlog will handle JSON rendering
            handlers=[console_handler, file_handler]
        )

        # Configure structlog for JSON structured logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to="event"),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        return structlog.get_logger(logger_name)

# Example usage of the CustomStructLogger 
if __name__ == "__main__":
    custom_struct_logger = CustomStructLogger()
    logger = custom_struct_logger.get_logger(__file__)
    logger.info("Custom struct logger initialized successfully.")