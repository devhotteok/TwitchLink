from Core import GlobalExceptions
from Services.NetworkRequests import Network
from Services.Twitch.Playback.PlaylistReader import PlaylistReader


class Exceptions(GlobalExceptions.Exceptions):
    class InvalidPlaylist(Exception):
        def __str__(self):
            return "Invalid Playlist"


class Segment:
    def __init__(self, fileName, duration, elapsedTime, muted):
        self.fileName = fileName
        self.duration = duration
        self.elapsedTime = elapsedTime
        self.muted = muted

    def getUnmutedFileName(self):
        return self.modifyFileName("{}-unmuted")

    def getMutedFileName(self):
        return self.modifyFileName("{}-muted")

    def modifyFileName(self, formatString):
        splitted = self.fileName.rsplit(".", 1)
        splitted[0] = formatString.format(splitted[0])
        return ".".join(splitted)

    def __str__(self):
        return f"<Segment {self.__dict__}>"

    def __repr__(self):
        return self.__str__()


class PlaylistData:
    class Range:
        def __init__(self):
            self.setRange()

        def setRange(self, timeFrom=None, timeTo=None):
            self.timeFrom = timeFrom
            self.timeTo = timeTo

    def __init__(self):
        self.playlist = ""
        self.segments = []
        self.totalSeconds = 0.0
        self.timeRange = self.Range()

    def getSegments(self):
        return self.segments

    def getFileList(self):
        return [segment.fileName for segment in self.segments]


class Playlist(PlaylistReader, PlaylistData):
    def __init__(self, url, filePath):
        super(Playlist, self).__init__()
        self.url = url
        self.filePath = filePath
        self.original = PlaylistData()
        self.openFile()
        self.updatePlaylist()

    def openFile(self):
        try:
            self.playlistFile = open(self.filePath, "w")
        except:
            raise Exceptions.FileSystemError

    def closeFile(self):
        try:
            self.playlistFile.close()
        except:
            raise Exceptions.FileSystemError

    def updatePlaylist(self):
        try:
            data = Network.session.get(self.url)
            if data.status_code != 200:
                raise
        except:
            raise Exceptions.NetworkError
        self.readPlaylist(self.verifyPlaylist(data.text))

    def verifyPlaylist(self, text):
        hasRequiredTags = {
            "EXTM3U": False,
            "EXT-X-TARGETDURATION": False,
            "EXT-X-ENDLIST": False
        }
        playlist = []
        for line in text.split("\n"):
            tag = self.getTag(line)
            if tag != None:
                if tag.name in hasRequiredTags:
                    hasRequiredTags[tag.name] = True
            playlist.append(line)
        if not all(hasRequiredTags.values()):
            raise Exceptions.InvalidPlaylist
        return playlist

    def readPlaylist(self, playlist):
        unmutedPlaylist = []
        segments = []
        expectSegment = None
        elapsedTime = 0.0
        for line in playlist:
            tag = self.getTag(line)
            if tag != None:
                if tag.name == "EXTINF":
                    try:
                        expectSegment = float(tag.data[0])
                    except:
                        pass
            elif expectSegment != None:
                muted = False
                splittedUrl = line.replace("\\", "/").rsplit("/", 1)
                splittedFileName = splittedUrl[-1].rsplit(".", 1)
                for key in ["-muted", "-unmuted"]:
                    if splittedFileName[0].endswith(key):
                        muted = True
                        splittedFileName[0] = splittedFileName[0][:-len(key)]
                        splittedUrl[-1] = ".".join(splittedFileName)
                        line = "/".join(splittedUrl)
                        break
                segments.append(Segment(line, expectSegment, elapsedTime, muted))
                elapsedTime += expectSegment
                expectSegment = None
            unmutedPlaylist.append(line)
        self.original.playlist = unmutedPlaylist
        self.original.segments = segments
        self.original.totalSeconds = elapsedTime
        self.updateRange()

    def setRange(self, timeFrom=None, timeTo=None):
        if timeFrom != None and timeTo != None:
            if timeFrom > timeTo:
                timeFrom, timeTo = timeTo, timeFrom
        self.original.timeRange.setRange(timeFrom, timeTo)
        self.updateRange()

    def updateRange(self):
        timeFrom = self.original.timeRange.timeFrom
        segmentFrom = None
        if timeFrom != None:
            for index, segment in reversed(list(enumerate(self.original.segments))):
                if segment.elapsedTime < timeFrom:
                    timeFrom = segment.elapsedTime
                    segmentFrom = index
                    break
        timeTo = self.original.timeRange.timeTo
        segmentTo = None
        if timeTo != None:
            for index, segment in enumerate(self.original.segments):
                if segment.elapsedTime > timeTo:
                    timeTo = segment.elapsedTime
                    segmentTo = index
                    break
        self.segments = self.original.segments[segmentFrom:segmentTo]
        self.totalSeconds = sum(segment.duration for segment in self.segments)
        if timeTo != None:
            timeTo = min(timeTo, self.original.totalSeconds)
        self.timeRange.setRange(timeFrom, timeTo)
        fileList = self.getFileList()
        originalFileList = self.original.getFileList()
        newPlaylist = []
        segment = None
        saveLines = True
        for line in self.original.playlist:
            tag = self.getTag(line)
            if tag != None:
                if tag.name == "EXTINF":
                    segment = line
                    continue
            if segment != None:
                if len(originalFileList) != 0:
                    if line in fileList:
                        newPlaylist.append(segment)
                        newPlaylist.append(line)
                        if line == fileList[-1] and line != originalFileList[-1]:
                            saveLines = False
                        else:
                            saveLines = True
                    elif line == originalFileList[-1]:
                        saveLines = True
                    else:
                        saveLines = False
                    segment = None
                    continue
            if saveLines:
                newPlaylist.append(line)
        self.playlist = newPlaylist
        self.saveAsFile()

    def saveAsFile(self):
        try:
            self.playlistFile.seek(0)
            self.playlistFile.truncate()
            self.playlistFile.write("\n".join(self.playlist))
            self.playlistFile.flush()
        except:
            raise Exceptions.FileSystemError