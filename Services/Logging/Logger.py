from .Handler import StreamHandler, FileHandler
from .Config import Config

from Services.Utils.OSUtils import OSUtils

from PyQt5 import QtCore

import logging
import time


class Logger:
    logging.Formatter.converter = time.gmtime

    def __init__(self, name="", directory=Config.LOG_ROOT, fileName="", propagate=False):
        self.logger = logging.getLogger(name)
        self.debug = self.logger.debug
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical
        self.exception = self.logger.exception
        if fileName == "":
            self.filePath = ""
        else:
            OSUtils.createDirectory(directory)
            self.filePath = OSUtils.joinPath(directory, fileName)
        if not self.logger.handlers:
            self.logger.propagate = propagate
            self.logger.setLevel(logging.DEBUG)
            for handler in Config.STREAM_HANDLERS:
                if self.filterHandler(handler):
                    self.logger.addHandler(StreamHandler(
                        minLevel=handler["minLevel"],
                        maxLevel=handler["maxLevel"],
                        formatString=handler["formatString"]
                    ))
            if self.filePath == "":
                return
            for handler in Config.FILE_HANDLERS:
                if self.filterHandler(handler):
                    self.logger.addHandler(FileHandler(
                        self.filePath,
                        minLevel=handler["minLevel"],
                        maxLevel=handler["maxLevel"],
                        formatString=handler["formatString"]
                    ))

    def filterHandler(self, handler):
        if "target" in handler:
            if handler["target"] == Config.TARGET_ROOT and self.logger != logging.root:
                return False
            if handler["target"] == Config.TARGET_NOT_ROOT and self.logger == logging.root:
                return False
        return True

    def getPath(self):
        return self.filePath

    @classmethod
    def getFormattedTime(cls):
        return QtCore.QDateTime.currentDateTimeUtc().toString("yyyy.MM.dd_HH-mm-ss")