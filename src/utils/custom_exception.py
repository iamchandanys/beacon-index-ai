import sys
import traceback

class CustomException(Exception):
    def __init__(self, error_message: str, error_details: sys):
        _,_,exc_traceback = error_details.exc_info() # Extract exc_traceback from exc_info() tuple.
        self.file_name = exc_traceback.tb_frame.f_code.co_filename
        self.line_number = exc_traceback.tb_lineno
        self.error_message = error_message
        self.traceback_str = ''.join(traceback.format_exception(*error_details.exc_info()))

    # The __str__ method returns a formatted string representation of the CustomException instance.
    # It provides a clear and informative description of the exception, useful for debugging, logging, or displaying error/other details.
    def __str__(self):
        return (
            f"\n--- Custom Exception ---\n"
            f"File      : {self.file_name}\n"
            f"Line      : {self.line_number}\n"
            f"Message   : {self.error_message}\n"
            f"Traceback :\n{self.traceback_str}"
        )