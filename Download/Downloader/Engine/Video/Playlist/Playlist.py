from Services.Twitch.Playback.PlaylistReader import PlaylistTagReader


class Exceptions:
    class InvalidPlaylist(Exception):
        def __str__(self):
            return "Invalid Playlist"


class Segment:
    def __init__(self, fileName, totalDurationMilliseconds, startsAt, muted, trimFromStart=None, trimFromEnd=None):
        self.fileName = fileName
        self.totalDurationMilliseconds = totalDurationMilliseconds
        self.durationMilliseconds = self.totalDurationMilliseconds - (trimFromStart or 0) - (trimFromEnd or 0)
        self.startsAt = startsAt
        self.endsAt = self.durationMilliseconds + self.startsAt
        self.muted = muted
        self.trimFromStart = trimFromStart
        self.trimFromEnd = trimFromEnd

    @property
    def trimmed(self):
        return not (self.trimFromStart == self.trimFromEnd == None)

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


class Playlist(PlaylistTagReader):
    class Range:
        def __init__(self):
            self.setRange()

        def setRange(self, timeFrom=None, timeTo=None):
            self.timeFrom = timeFrom
            self.timeTo = timeTo

        def getRange(self):
            return (self.timeFrom, self.timeTo)

    def __init__(self, text=None):
        super(Playlist, self).__init__()
        self.playlist = []
        self.segments = []
        self.totalMilliseconds = 0
        self.timeRange = self.Range()
        if text != None:
            self.readPlaylist(text)

    @property
    def totalSeconds(self):
        return self.totalMilliseconds / 1000

    def getSegments(self):
        return self.segments

    def getFileList(self):
        return [segment.fileName for segment in self.segments]

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

    def readPlaylist(self, text):
        playlist = self.verifyPlaylist(text)
        unmutedPlaylist = []
        segments = []
        expectSegment = None
        elapsedMilliseconds = 0
        for line in playlist:
            tag = self.getTag(line)
            if tag != None:
                if tag.name == "EXTINF":
                    try:
                        expectSegment = int(float(tag.data[0]) * 1000)
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
                segments.append(Segment(line, expectSegment, elapsedMilliseconds, muted))
                elapsedMilliseconds += expectSegment
                expectSegment = None
            unmutedPlaylist.append(line)
        self.playlist = unmutedPlaylist
        self.segments = segments
        self.totalMilliseconds = elapsedMilliseconds

    def setRange(self, timeFrom=None, timeTo=None):
        if timeFrom != None and timeTo != None:
            if timeFrom > timeTo:
                timeFrom, timeTo = timeTo, timeFrom
        self.timeRange.setRange(timeFrom, timeTo)

    def getRangedPlaylist(self):
        millisecondsFrom = self.timeRange.timeFrom
        millisecondsTo = self.timeRange.timeTo
        segmentFrom = None
        trimFromStart = 0
        segmentTo = None
        trimFromEnd = 0
        if millisecondsFrom != None:
            for index, segment in reversed(list(enumerate(self.segments))):
                if segment.startsAt <= millisecondsFrom:
                    segmentFrom = index
                    trimFromStart = millisecondsFrom - segment.startsAt
                    break
        if millisecondsTo != None:
            for index, segment in enumerate(self.segments):
                if segment.endsAt >= millisecondsTo:
                    segmentTo = index
                    trimFromEnd = segment.endsAt - millisecondsTo
                    break
        rangedSegments = self.segments[segmentFrom:None if segmentTo == None else segmentTo + 1]
        newSegments = []
        totalMilliseconds = 0
        for index, segment in enumerate(rangedSegments):
            if index == 0:
                segmentTrimFromStart = trimFromStart or None
            else:
                segmentTrimFromStart = None
            if index == len(rangedSegments) - 1:
                segmentTrimFromEnd = trimFromEnd or None
            else:
                segmentTrimFromEnd = None
            newSegment = Segment(segment.fileName, segment.totalDurationMilliseconds, totalMilliseconds, segment.muted, trimFromStart=segmentTrimFromStart, trimFromEnd=segmentTrimFromEnd)
            totalMilliseconds += newSegment.durationMilliseconds
            newSegments.append(newSegment)
        rangedFileList = [segment.fileName for segment in newSegments]
        originalFileList = self.getFileList()
        newPlaylist = []
        segmentTag = None
        saveLines = True
        for line in self.playlist:
            tag = self.getTag(line)
            if tag != None:
                if tag.name == "EXTINF":
                    segmentTag = tag
                    continue
            if segmentTag != None:
                if len(originalFileList) != 0:
                    if line in rangedFileList:
                        lineSegment = newSegments[rangedFileList.index(line)]
                        if lineSegment.trimmed:
                            segmentTag.data[0] = f"{lineSegment.durationMilliseconds / 1000:.3f}"
                        newPlaylist.append(segmentTag.toString())
                        newPlaylist.append(line)
                        if line == rangedFileList[-1] and line != originalFileList[-1]:
                            saveLines = False
                        else:
                            saveLines = True
                    elif line == originalFileList[-1]:
                        saveLines = True
                    else:
                        saveLines = False
                    segmentTag = None
                    continue
            if saveLines:
                newPlaylist.append(line)
        rangedPlaylist = Playlist()
        rangedPlaylist.playlist = newPlaylist
        rangedPlaylist.segments = newSegments
        rangedPlaylist.totalMilliseconds = totalMilliseconds
        return rangedPlaylist