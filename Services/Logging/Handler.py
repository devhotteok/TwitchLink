from .Filter import RangeFilter

import logging


class StreamHandler(logging.StreamHandler):
    def __init__(self, minLevel=logging.DEBUG, maxLevel=logging.CRITICAL, formatString=None):
        super(StreamHandler, self).__init__()
        self.setLevel(minLevel)
        self.setFormatter(logging.Formatter(formatString))
        self.addFilter(RangeFilter(minLevel, maxLevel))


class FileHandler(logging.FileHandler):
    def __init__(self, filePath, minLevel=logging.DEBUG, maxLevel=logging.CRITICAL, formatString=None):
        super(FileHandler, self).__init__(filePath, encoding="utf-8")
        self.setLevel(minLevel)
        self.setFormatter(logging.Formatter(formatString))
        self.addFilter(RangeFilter(minLevel, maxLevel))