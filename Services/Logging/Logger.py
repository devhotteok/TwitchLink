from .Handler import StreamHandler, FileHandler
from .Config import Config

from Services.Utils.OSUtils import OSUtils

import logging
import datetime


class Logger:
    def __init__(self, name="", directory=Config.LOG_ROOT, fileName=""):
        self.logger = logging.getLogger(name)
        self.debug = self.logger.debug
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.critical = self.logger.critical
        self.exception = self.logger.exception
        if not self.logger.handlers:
            self.logger.propagate = False
            self.logger.setLevel(logging.DEBUG)
            for handler in Config.STREAM_HANDLERS:
                if self.filterHandler(handler):
                    self.logger.addHandler(StreamHandler(
                        minLevel=handler["minLevel"],
                        maxLevel=handler["maxLevel"],
                        formatString=handler["formatString"]
                    ))
            if fileName == "":
                self.filePath = ""
                return
            OSUtils.createDirectory(directory)
            self.filePath = OSUtils.joinPath(directory, fileName)
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
        return datetime.datetime.now().strftime("%Y.%m.%d_%H-%M-%S")