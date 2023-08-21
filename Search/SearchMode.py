import enum


class SearchMode:
    class Types(enum.Enum):
        CHANNEL = "channel"
        VIDEO = "video"
        CLIP = "clip"
        URL = "url"
        UNKNOWN = "unknown"

    def __init__(self, searchMode: Types):
        self.setMode(searchMode)

    def setMode(self, searchMode: Types) -> None:
        self._searchMode = searchMode

    def getMode(self) -> Types:
        return self._searchMode

    def isChannel(self) -> bool:
        return self._searchMode == self.Types.CHANNEL

    def isVideo(self) -> bool:
        return self._searchMode == self.Types.VIDEO

    def isClip(self) -> bool:
        return self._searchMode == self.Types.CLIP

    def isUrl(self) -> bool:
        return self._searchMode == self.Types.URL

    def isUnknown(self) -> bool:
        return self._searchMode == self.Types.UNKNOWN