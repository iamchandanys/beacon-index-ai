import os
import logging
from datetime import datetime

class CustomLogger:
    def __init__(self):
        logs_dir = os.path.join(os.getcwd(), "logs")
        
        os.makedirs(logs_dir, exist_ok=True)  
        
        LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        
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