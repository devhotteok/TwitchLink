from PyQt6 import QtCore


class Segment:
    def __init__(self, sequence: int, url: QtCore.QUrl, datetime: QtCore.QDateTime | None, totalMilliseconds: int, startsAt: int, title: str = ""):
        self.sequence = sequence
        self.url = url
        self.datetime = datetime
        self.totalMilliseconds = totalMilliseconds
        self.startsAt = startsAt
        self.title = title

    @property
    def endsAt(self) -> int:
        return self.startsAt + self.totalMilliseconds

    def __str__(self):
        return f"<Segment {self.__dict__}>"

    def __repr__(self):
        return self.__str__()