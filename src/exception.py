import sys

def error_msg_detail(error,error_detail:sys):
    _,_,exc_tb = error_detail.exc_info()
    if exc_tb is not None:
        file_name = exc_tb.tb_frame.f_code.co_filename
        error_message = "Error Occured in [{0}] at line [{1}] with error [{2}]".format(
            file_name,
            exc_tb.tb_lineno,
            str(error)
        )
    else:
        error_message = "Error occurred: {0}".format(str(error))
    return error_message

class CustomException(Exception):
    def __init__(self, error_message,error_detail:sys):
        super().__init__(error_message)
        self.error_message = error_msg_detail(error_message,error_detail=error_detail)
    def __str__(self):
        return self.error_message