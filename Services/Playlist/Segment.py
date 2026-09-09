from PyQt6 import QtCore


class Segment:
    def __init__(self, sequence: int, url: QtCore.QUrl, datetime: QtCore.QDateTime | None, totalMilliseconds: int, startsAt: int, mapInfo: str | None = None, title: str = "", initializationSegment: bool = False):
        self.sequence = sequence
        self.url = url
        self.datetime = datetime
        self.totalMilliseconds = totalMilliseconds
        self.startsAt = startsAt
        self.mapInfo = mapInfo
        self.title = title
        self._initializationSegment = initializationSegment

    @property
    def endsAt(self) -> int:
        return self.startsAt + self.totalMilliseconds

    def isInitializationSegment(self) -> bool:
        return self._initializationSegment

    def __str__(self):
        return f"<Segment {self.__dict__}>"

    def __repr__(self):
        return self.__str__()