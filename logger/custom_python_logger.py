import os
import logging
from datetime import datetime
import structlog

class CustomLogger:
    def __init__(self):
        # Initialize the logs directory
        logs_dir = os.path.join(os.getcwd(), "logs")
        
        # Create the logs directory if it doesn't exist
        os.makedirs(logs_dir, exist_ok=True)  
        
        # Generate the log file name with timestamp
        LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        
        # Set the full path for the log file
        LOG_FILE_PATH = os.path.join(logs_dir, LOG_FILE)
        
        logging.basicConfig(
            filename=LOG_FILE_PATH,
            format="[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
            level=logging.DEBUG,  # Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        )
    
    def get_logger(self, name=__file__):
        return logging.getLogger(os.path.basename(name))

# Example usage of the CustomLogger
if __name__ == "__main__":
    custom_logger = CustomLogger()
    logger = custom_logger.get_logger(__file__)
    logger.info("Custom logger initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")