from .Handler import StreamHandler, FileHandler
from .Config import Config

from Services.Utils.OSUtils import OSUtils

from PyQt6 import QtCore

import typing
import logging
import time
import json


class Logger:
    instanceList = {}

    logging.Formatter.converter = time.gmtime

    def __init__(self, name: str = "", directory: str = Config.LOG_ROOT, fileName: str = "", propagate: bool = False):
        self.logger = logging.getLogger(name)
        self._isRoot = self.logger == logging.root
        if not self._isRoot:
            if self.logger.name not in self.instanceList:
                self.instanceList[self.logger.name] = 0
            self.instanceList[self.logger.name] += 1
        self.debug = self.logger.debug
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical
        self.exception = self.logger.exception
        if fileName == "":
            self.filePath = ""
        else:
            try:
                OSUtils.createDirectory(directory)
            except:
                pass
            self.filePath = OSUtils.joinPath(directory, fileName)
        if len(self.logger.handlers) == 0:
            self.logger.propagate = propagate
            self.logger.setLevel(logging.DEBUG)
            for handler in Config.STREAM_HANDLERS:
                if self._filterHandler(handler):
                    self.logger.addHandler(StreamHandler(
                        minLevel=handler["minLevel"],
                        maxLevel=handler["maxLevel"],
                        formatString=handler["formatString"]
                    ))
            if self.filePath == "":
                return
            for handler in Config.FILE_HANDLERS:
                if self._filterHandler(handler):
                    self.logger.addHandler(FileHandler(
                        self.filePath,
                        minLevel=handler["minLevel"],
                        maxLevel=handler["maxLevel"],
                        formatString=handler["formatString"]
                    ))

    def getPath(self) -> str:
        return self.filePath

    @classmethod
    def getFormattedTime(cls) -> str:
        return QtCore.QDateTime.currentDateTimeUtc().toString("yyyy.MM.dd_HH-mm-ss")

    @classmethod
    def generateObjectLog(cls, target: typing.Any) -> str:
        return json.dumps(cls._getObjectData(target), indent=3, ensure_ascii=False)

    def _filterHandler(self, handler: dict) -> bool:
        if "target" in handler:
            if handler["target"] == Config.TARGET_ROOT and self.logger != logging.root:
                return False
            if handler["target"] == Config.TARGET_NOT_ROOT and self.logger == logging.root:
                return False
        return True

    @classmethod
    def _getObjectData(cls, target: typing.Any) -> typing.Any:
        if isinstance(target, dict):
            return {key: Config.REPLACEMENT_STRING.format(dataType=key.lower()) if key.lower() in Config.SECURITY_REPLACEMENTS else cls._getObjectData(value) for key, value in target.items()}
        elif isinstance(target, list):
            return [cls._getObjectData(data) for data in target]
        elif isinstance(target, QtCore.QDateTime):
            return target.toString(QtCore.Qt.DateFormat.ISODateWithMs)
        elif hasattr(target, "__dict__"):
            return cls._getObjectData(target.__dict__)
        else:
            return target

    def __del__(self):
        if not self._isRoot:
            self.instanceList[self.logger.name] -= 1
            if self.instanceList[self.logger.name] == 0:
                self.instanceList.pop(self.logger.name)
                while len(self.logger.handlers) != 0:
                    self.logger.removeHandler(self.logger.handlers[0])