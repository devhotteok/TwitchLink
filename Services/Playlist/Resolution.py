from AppData.EncoderDecoder import Serializable

from PyQt6 import QtCore

import re


class Resolution(Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    RESOLUTION_TEXT = re.compile("(\d+)p(\d+(?:\.\d+)?)")

    def __init__(self, name: str, groupId: str, url: QtCore.QUrl, autoSelect: bool = True, default: bool = True):
        self.name: str = name
        self.groupId: str = groupId
        self.url: QtCore.QUrl = url
        self.autoSelect: bool = autoSelect
        self.default: bool = default
        self.quality: int | None = None
        self.frameRate: int | None = None
        self._parseResolution()

    def _parseResolution(self) -> None:
        self.quality = None
        self.frameRate = None
        for string in [self.groupId, self.name]:
            tag = re.search(self.RESOLUTION_TEXT, string)
            if tag != None:
                self.quality = int(tag.group(1))
                self.frameRate = None if tag.group(2) == None else round(float(tag.group(2)))
                if self.frameRate != None:
                    return

    def isSource(self) -> bool:
        return self.groupId == "chunked"

    def isAudioOnly(self) -> bool:
        return self.groupId == "audio_only"

    @property
    def displayName(self) -> str:
        return self.name if self.quality == None or self.frameRate == None else f"{self.quality}p{self.frameRate}"

    def __lt__(self, other):
        return (self.isSource(), self.quality or 0, self.frameRate or 0) < (other.isSource(), other.quality or 0, other.frameRate or 0)

    def __le__(self, other):
        return (self.isSource(), self.quality or 0, self.frameRate or 0) <= (other.isSource(), other.quality or 0, other.frameRate or 0)

    def __gt__(self, other):
        return (self.isSource(), self.quality or 0, self.frameRate or 0) > (other.isSource(), other.quality or 0, other.frameRate or 0)

    def __ge__(self, other):
        return (self.isSource(), self.quality or 0, self.frameRate or 0) >= (other.isSource(), other.quality or 0, other.frameRate or 0)

    def __eq__(self, other):
        if isinstance(other, Resolution):
            return (self.isSource(), self.quality or 0, self.frameRate or 0) == (other.isSource(), other.quality or 0, other.frameRate or 0)
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Resolution):
            return (self.isSource(), self.quality or 0, self.frameRate or 0) != (other.isSource(), other.quality or 0, other.frameRate or 0)
        else:
            return NotImplemented