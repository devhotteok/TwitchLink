from .PlaylistTagReader import PlaylistTag, PlaylistTagReader
from .Segment import Segment

from PyQt6 import QtCore

import typing


class Exceptions:
    class InvalidPlaylist(Exception):
        def __str__(self):
            return "Invalid Playlist"


class Playlist:
    def __init__(self):
        self._version: int = 3
        self._targetDuration: int = 0
        self._endList = False
        self._segments: list[Segment] = []

    def setVersion(self, version: int) -> None:
        self._version = version

    def getVersion(self) -> int:
        return self._version

    def setTargetDuration(self, targetDuration: int) -> None:
        self._targetDuration = targetDuration

    def getTargetDuration(self) -> int:
        return self._targetDuration

    def getMediaSequence(self) -> int:
        return 0 if len(self._segments) == 0 else self._segments[0].sequence

    def setEndList(self, endList: bool) -> None:
        self._endList = endList

    def isEndList(self) -> bool:
        return self._endList

    def setSegments(self, segments: list[Segment]) -> None:
        self._segments = segments

    def getSegments(self) -> list[Segment]:
        return self._segments

    @property
    def totalMilliseconds(self) -> int:
        return 0 if len(self._segments) == 0 else self._segments[-1].endsAt

    @property
    def totalSeconds(self) -> float:
        return self.totalMilliseconds / 1000

    def loads(self, text: str, baseUrl: QtCore.QUrl | None = None) -> None:
        try:
            lines = text.splitlines()
            version = 3
            targetDuration = 0
            mediaSequence = 0
            mapInfo = None
            endList = False
            segments = []
            expectSegment = []
            elapsedMilliseconds = 0
            assert PlaylistTagReader.getTag(lines[0]) == PlaylistTag("EXTM3U")
            for line in lines:
                tag = PlaylistTagReader.getTag(line)
                if tag != None:
                    if tag.name == "EXT-X-VERSION":
                        version = int(tag.data[0])
                    elif tag.name == "EXT-X-TARGETDURATION":
                        targetDuration = int(tag.data[0])
                    elif tag.name == "EXT-X-MEDIA-SEQUENCE":
                        mediaSequence = int(tag.data[0])
                    elif tag.name == "EXT-X-MAP":
                        mapInfo = tag.data.get("URI") or None
                    elif tag.name == "EXT-X-ENDLIST":
                        endList = True
                    elif tag.name == "EXT-X-PROGRAM-DATE-TIME":
                        expectSegment.append(tag)
                    elif tag.name == "EXTINF":
                        expectSegment.append(tag)
                    elif tag.name == "EXT-X-DISCONTINUITY":
                        pass
                elif len(expectSegment) != 0:
                    programDateTime = None
                    durationMilliseconds = None
                    for tag in expectSegment:
                        if tag.name == "EXT-X-PROGRAM-DATE-TIME":
                            programDateTime = QtCore.QDateTime.fromString(tag.data[0], QtCore.Qt.DateFormat.ISODateWithMs)
                        elif tag.name == "EXTINF":
                            durationMilliseconds = int(float(tag.data[0]) * 1000)
                    if durationMilliseconds == None:
                        continue
                    segments.append(Segment(mediaSequence + len(segments), QtCore.QUrl(line) if baseUrl == None else baseUrl.resolved(QtCore.QUrl(line)), programDateTime, durationMilliseconds, elapsedMilliseconds, mapInfo, tag.data[1]))
                    elapsedMilliseconds += durationMilliseconds
                    expectSegment.clear()
        except:
            raise Exceptions.InvalidPlaylist
        else:
            self.setVersion(version)
            self.setTargetDuration(targetDuration)
            self.setEndList(endList)
            self.setSegments(segments)

    def getSegmentRange(self, mSecsFrom: int | None = None, mSecsTo: int | None = None) -> tuple[int | None, int | None]:
        if mSecsFrom != None:
            if mSecsFrom > self.totalMilliseconds:
                mSecsFrom = self.totalMilliseconds
            else:
                for segment in self._segments:
                    if segment.endsAt > mSecsFrom:
                        mSecsFrom = segment.startsAt
                        break
        if mSecsTo != None:
            if mSecsTo > self.totalMilliseconds:
                mSecsTo = self.totalMilliseconds
            else:
                for segment in reversed(self._segments):
                    if segment.startsAt < mSecsTo:
                        mSecsTo = segment.endsAt
                        break
        return mSecsFrom, mSecsTo

    def getRangedSegments(self, mSecsFrom: int | None = None, mSecsTo: int | None = None) -> typing.Generator[Segment, None, None]:
        mSecsFrom = mSecsFrom or 0
        mSecsTo = mSecsTo or self.totalMilliseconds
        for segment in self.getSegments():
            if segment.startsAt < mSecsTo and segment.endsAt > mSecsFrom:
                yield segment