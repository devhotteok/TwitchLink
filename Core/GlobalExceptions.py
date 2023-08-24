from PyQt6 import QtCore, QtNetwork


class Exceptions:
    class UnexpectedError(Exception):
        def __init__(self, exception: str | Exception | None = None):
            self.exception = exception

        def __str__(self):
            return f"Unexpected Error: {self.exception}"

    class FileSystemError(Exception):
        def __init__(self, target: QtCore.QFile | QtCore.QTemporaryFile | QtCore.QDir):
            if isinstance(target, QtCore.QFile) or isinstance(target, QtCore.QTemporaryFile):
                self.exceptionType = target.error()
                self.reasonText = target.errorString()
            else:
                self.exceptionType = "Directory Error"
                reasonText = f"Unable to create directory '{target.path()}'."
                self.reasonText = f"{reasonText}\nThis directory already exists." if target.exists() else reasonText

        def __str__(self):
            return f"File System Error: {self.exceptionType}\n{self.reasonText}"

    class NetworkError(Exception):
        def __init__(self, reply: QtNetwork.QNetworkReply):
            self.reasonCode = reply.error()
            self.reasonText = reply.errorString()
            self.responseText = "" if self.reasonCode == QtNetwork.QNetworkReply.NetworkError.OperationCanceledError else reply.readAll().data().decode()

        def __str__(self):
            if self.responseText == "":
                return f"Network Error: {self.reasonCode}\n{self.reasonText}"
            else:
                return f"Network Error: {self.reasonCode}\n{self.reasonText}\n{self.responseText}"

    class ProcessError(Exception):
        def __init__(self, process: QtCore.QProcess):
            self.exitCode = process.exitCode()
            self.name = process.error().name
            self.value = process.error().value
            self.info = process.errorString()

        def __str__(self):
            return f"Process Error\nExitCode: {self.exitCode}\nError: {self.name}: {self.value}\n{self.info}"

    class AbortRequested(Exception):
        def __init__(self, reason: str | None = None):
            self.reason = reason

        def __str__(self):
            return "Abort Requested" if self.reason == None else f"Abort Requested: {self.reason}"