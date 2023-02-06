from Database.EncoderDecoder import Codable


class TwitchPlaybackObject(Codable):
    CODABLE_INIT_MODEL = False
    CODABLE_STRICT_MODE = False

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()


class TwitchPlaybackAccessTokenTypes(TwitchPlaybackObject):
    STREAM = "stream"
    VIDEO = "video"
    CLIP = "clip"

    def __init__(self, tokenType):
        self.setType(tokenType)

    def setType(self, tokenType):
        self._tokenType = tokenType

    def getType(self):
        return self._tokenType

    def isStream(self):
        return self._tokenType == self.STREAM

    def isVideo(self):
        return self._tokenType == self.VIDEO

    def isClip(self):
        return self._tokenType == self.CLIP

    def toString(self):
        return self.getType()


class Resolution(TwitchPlaybackObject):
    def __init__(self, name, groupId, url, autoSelect=True, default=True):
        self.name = name
        self.groupId = groupId
        self.url = url
        self.autoSelect = autoSelect
        self.default = default
        self._parseResolution()

    def _parseResolution(self):
        for parseString in [self.groupId, self.name]:
            try:
                parsed = parseString.split("p", 1)
                self.quality = int(parsed[0])
                try:
                    self.frameRate = int(parsed[1])
                except:
                    self.frameRate = None
                return
            except:
                pass
        self.quality = None
        self.frameRate = None

    def isSource(self):
        return self.groupId == "chunked"

    def isAudioOnly(self):
        return self.groupId == "audio_only"

    @property
    def displayName(self):
        newString = ""
        brackets = 0
        for char in self.name:
            if char == "(":
                brackets += 1
                continue
            elif char == ")":
                brackets -= 1
                continue
            if brackets == 0:
                newString += char
            elif brackets < 0:
                return self.name
        if brackets == 0:
            return " ".join(newString.split())
        else:
            return self.name


class StreamUrl(Resolution):
    def __init__(self, channel, name, groupId, url, autoSelect=True, default=True):
        super(StreamUrl, self).__init__(name, groupId, url, autoSelect, default)
        self.channel = channel

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.channel}] [{self.name}]>"


class VideoUrl(Resolution):
    def __init__(self, videoId, name, groupId, url, autoSelect=True, default=True):
        super(VideoUrl, self).__init__(name, groupId, url, autoSelect, default)
        self.videoId = videoId

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.videoId}] [{self.name}]>"


class ClipUrl(Resolution):
    def __init__(self, slug, name, url):
        super(ClipUrl, self).__init__(name, name, url)
        self.slug = slug

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.slug}] [{self.name}]>"