import sys
import traceback

from logger.custom_logger import CustomLogger

class CustomException(Exception):
    def __init__(self, error_message: str, error_details: sys):
        _,_,exc_traceback = error_details.exc_info()
        self.file_name = exc_traceback.tb_frame.f_code.co_filename
        self.line_number = exc_traceback.tb_lineno
        self.eror_message = error_message
        self.traceback_str = ''.join(traceback.format_exception(*error_details.exc_info()))
        
        # Initialize the custom logger
        customLogger = CustomLogger()
        self.logger = customLogger.get_logger(__file__)

    def __str__(self):
        return (
            f"\n--- Custom Exception ---\n"
            f"File      : {self.file_name}\n"
            f"Line      : {self.line_number}\n"
            f"Message   : {self.eror_message}\n"
            f"Traceback :\n{self.traceback_str}"
        )
        
# Example usage of the CustomException
if __name__ == "__main__":
    try:
        # Simulate an error
        1 / 0
    except Exception as e:
        custom_exception = CustomException(str(e), sys)
        custom_exception.logger.error(custom_exception)
        raise custom_exception