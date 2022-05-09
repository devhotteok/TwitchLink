class SearchModes:
    CHANNEL = "channel"
    VIDEO = "video"
    CLIP = "clip"
    URL = "url"

    def __init__(self, searchMode):
        self.setMode(searchMode)

    def setMode(self, searchMode):
        self._searchMode = searchMode

    def getMode(self):
        return self._searchMode

    def isChannel(self):
        return self._searchMode == self.CHANNEL

    def isVideo(self):
        return self._searchMode == self.VIDEO

    def isClip(self):
        return self._searchMode == self.CLIP

    def isUrl(self):
        return self._searchMode == self.URL