import logging


class RangeFilter(logging.Filter):
    def __init__(self, minLevel: int, maxLevel: int):
        super().__init__()
        self.minLevel = minLevel
        self.maxLevel = maxLevel

    def filter(self, record: logging.LogRecord) -> bool:
        return self.minLevel <= record.levelno <= self.maxLevel