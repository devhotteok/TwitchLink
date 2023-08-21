from .Filter import RangeFilter

import logging


class StreamHandler(logging.StreamHandler):
    def __init__(self, minLevel: int = logging.DEBUG, maxLevel: int = logging.CRITICAL, formatString: str | None = None):
        super().__init__()
        self.setLevel(minLevel)
        self.setFormatter(logging.Formatter(formatString))
        self.addFilter(RangeFilter(minLevel, maxLevel))


class FileHandler(logging.FileHandler):
    def __init__(self, filePath: str, minLevel: int = logging.DEBUG, maxLevel: int = logging.CRITICAL, formatString: str | None = None):
        super().__init__(filePath, encoding="utf-8")
        self.setLevel(minLevel)
        self.setFormatter(logging.Formatter(formatString))
        self.addFilter(RangeFilter(minLevel, maxLevel))