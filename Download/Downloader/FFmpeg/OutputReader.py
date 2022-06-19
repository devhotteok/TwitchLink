from .Exceptions import Exceptions

import re


class ProgressMessages:
    file = re.compile("\[.* @ .*\] Opening \'(.*)\' for reading")
    missing = re.compile("\[.* @ .*\] Failed to open segment (\d*) of playlist .*")
    encoding = re.compile(".*size=.*time=.*bitrate=.*speed=.*")



class ExceptionMessages:
    directory = "No such file or directory"
    permission = "Permission denied"


class FFmpegOutputReader:
    def __init__(self, process, logger=None):
        self.process = process
        self.logger = logger

    def reader(self):
        return self._read() if self.logger == None else self._readWithLogs()

    def _read(self):
        line = ""
        try:
            for line in self.process.stdout:
                progressData = self.getProgressData(line)
                if progressData != None:
                    yield progressData
        except:
            pass
        self.checkError(self.process.wait(), line)

    def _readWithLogs(self):
        line = ""
        try:
            for line in self.process.stdout:
                self.logger.debug(line.strip("\n"))
                progressData = self.getProgressData(line)
                if progressData != None:
                    yield progressData
        except Exception as e:
            self.logger.error("Unable to read output properly.")
            self.logger.exception(e)
        returnCode = self.process.wait()
        if self.process.notResponding:
            self.logger.info("Subprocess was unresponsive and forced to terminate.")
        self.logger.info(f"Subprocess ended with exit code {returnCode}.")
        self.checkError(returnCode, line)

    def checkError(self, returnCode, line):
        if returnCode == 0:
            return
        errorType = line.rsplit(":", 1)[-1].strip()
        if errorType == ExceptionMessages.directory or errorType == ExceptionMessages.permission:
            raise Exceptions.FileSystemError
        raise Exceptions.UnexpectedError

    def getProgressData(self, line):
        return self.getFileData(line) or self.getMissingData(line) or self.getEncodingData(line)

    def getFileData(self, line):
        checkFile = re.search(ProgressMessages.file, line)
        if checkFile == None:
            return None
        else:
            return {"file": checkFile.group(1)}

    def getMissingData(self, line):
        checkMissing = re.search(ProgressMessages.missing, line)
        if checkMissing == None:
            return None
        else:
            return {"missing": int(checkMissing.group(1))}

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