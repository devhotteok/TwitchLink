import logging


class RangeFilter(logging.Filter):
    def __init__(self, minLevel, maxLevel):
        super(RangeFilter, self).__init__()
        self.minLevel = minLevel
        self.maxLevel = maxLevel

    def filter(self, record):
        return self.minLevel <= record.levelno <= self.maxLevel