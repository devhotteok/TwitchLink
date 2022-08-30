from Core import GlobalExceptions


class Exceptions(GlobalExceptions.Exceptions):
    class UnexpectedError(Exception):
        def __init__(self, returnCode, line):
            self.returnCode = returnCode
            self.line = line

        def __str__(self):
            return f"Unexpected Error\nreturnCode: {self.returnCode}\noutput: {self.line}"