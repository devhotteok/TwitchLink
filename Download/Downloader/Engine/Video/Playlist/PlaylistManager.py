from .Playlist import Playlist

from Core.GlobalExceptions import Exceptions


class PlaylistManager:
    def __init__(self, text, filePath, strictMode=False):
        self.filePath = filePath
        self.strictMode = strictMode
        self.openFile()
        self.original = Playlist()
        self.readPlaylist(text)

    def readPlaylist(self, text):
        self.original.readPlaylist(text)
        self.playlistUpdated()

    def setRange(self, timeFrom=None, timeTo=None):
        self.original.setRange(timeFrom, timeTo)
        self.playlistUpdated()

    def isStrictMode(self):
        return self.strictMode

    def getSegments(self):
        return self.ranged.getSegments()

    def getFileList(self):
        return self.ranged.getFileList()

    @property
    def totalMilliseconds(self):
        if self.isStrictMode():
            return self.ranged.totalMilliseconds
        else:
            return self.getApproximateTotalMilliseconds()

    @property
    def totalSeconds(self):
        return self.totalMilliseconds / 1000

    def getTrimRange(self):
        if self.isStrictMode():
            trimFrom = self.ranged.segments[0].trimFromStart
            if self.ranged.segments[-1].trimFromEnd == None:
                trimTo = None
            else:
                trimTo = (trimFrom or 0) + self.totalMilliseconds
            return trimFrom, trimTo
        else:
            return None, None

    def getTimeRange(self):
        if self.isStrictMode():
            return self.original.timeRange.getRange()
        else:
            return self.getApproximateTimeRange()

    def getApproximateTimeRange(self):
        start, end = self.original.timeRange.getRange()
        if start != None:
            start -= self.ranged.segments[0].trimFromStart or 0
        if end != None:
            end += self.ranged.segments[-1].trimFromEnd or 0
        return start, end

    def getApproximateTotalMilliseconds(self):
        start, end = self.getApproximateTimeRange()
        return (end or self.ranged.totalMilliseconds) - (start or 0)

    def playlistUpdated(self):
        self.ranged = self.original.getRangedPlaylist()
        self.saveAsFile()

    def openFile(self):
        try:
            self.playlistFile = open(self.filePath, "w")
        except:
            raise Exceptions.FileSystemError

    def closeFile(self):
        if hasattr(self, "playlistFile"):
            if not self.playlistFile.closed:
                try:
                    self.playlistFile.close()
                except:
                    raise Exceptions.FileSystemError

    def saveAsFile(self):
        try:
            self.playlistFile.seek(0)
            self.playlistFile.truncate()
            self.playlistFile.write("\n".join(self.ranged.playlist))
            self.playlistFile.flush()
        except:
            raise Exceptions.FileSystemError

    def __del__(self):
        try:
            self.closeFile()
        except:
            pass