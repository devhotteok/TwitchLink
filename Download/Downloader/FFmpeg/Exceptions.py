from Core import GlobalExceptions


class Exceptions(GlobalExceptions.Exceptions):
    class UnexpectedError(Exception):
        def __str__(self):
            return "Unexpected Error"