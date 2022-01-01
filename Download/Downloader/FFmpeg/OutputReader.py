from .Exceptions import Exceptions

import re


class ProgressMessages:
    file = re.compile("\[.* @ .*\] Opening \'(.*)\' for reading")
    encoding = re.compile(".*size=.*time=.*bitrate=.*speed=.*")


class ExceptionMessages:
    directory = "No such file or directory"
    permission = "Permission denied"


class FFmpegOutputReader:
    def __init__(self, process):
        self.process = process

    def reader(self):
        line = ""
        for line in self.process.stdout:
            progressData = self.getProgressData(line)
            if progressData != None:
                yield progressData
        self.checkError(self.process.wait(), line)

    def checkError(self, returnCode, line):
        if returnCode == 0:
            return
        errorType = line.rsplit(":", 1)[-1].strip()
        if errorType == ExceptionMessages.directory or errorType == ExceptionMessages.permission:
            raise Exceptions.FileSystemError
        raise Exceptions.UnexpectedError

    def getProgressData(self, line):
        return self.getFileData(line) or self.getEncodingData(line)

    def getFileData(self, line):
        checkFile = re.search(ProgressMessages.file, line)
        if checkFile == None:
            return None
        else:
            return {"file": checkFile.group(1)}

    def getEncodingData(self, line):
        checkEncoding = re.search(ProgressMessages.encoding, line)
        if checkEncoding == None:
            return None
        progressData = {}
        previousKey = None
        for data in map(str.strip, line.split()):
            if "=" in data:
                if data.endswith("="):
                    previousKey = data.split("=", 1)[0]
                    progressData[previousKey] = ""
                else:
                    key, value = data.split("=", 1)
                    progressData[key] = value
                    previousKey = None
            else:
                if previousKey != None:
                    progressData[previousKey] = data
                    previousKey = None
        return progressData