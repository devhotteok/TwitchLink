class SearchModes:
    class MODES:
        CHANNEL = "channel"
        VIDEO = "video"
        CLIP = "clip"
        URL = "url"

    CHANNEL = lambda: SearchModes(SearchModes.MODES.CHANNEL)
    VIDEO = lambda: SearchModes(SearchModes.MODES.VIDEO)
    CLIP = lambda: SearchModes(SearchModes.MODES.CLIP)
    URL = lambda: SearchModes(SearchModes.MODES.URL)

    def __init__(self, searchMode):
        self.setMode(searchMode)

    def setMode(self, searchMode):
        self._searchMode = searchMode

    def getMode(self):
        return self._searchMode

    def isChannel(self):
        return self._searchMode == self.MODES.CHANNEL

    def isVideo(self):
        return self._searchMode == self.MODES.VIDEO

    def isClip(self):
        return self._searchMode == self.MODES.CLIP

    def isUrl(self):
        return self._searchMode == self.MODES.URL