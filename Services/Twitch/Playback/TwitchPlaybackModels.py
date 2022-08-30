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

class StreamUrl(TwitchPlaybackObject):
    def __init__(self, channel, resolutionName, url, data, source, chunked, audioOnly):
        self.channel = channel
        self.resolutionName = resolutionName
        self.url = url
        self.data = data
        self.source = source
        self.chunked = chunked
        self.audioOnly = audioOnly

    @property
    def displayName(self):
        name = self.resolutionName
        if self.source:
            name = f"{name} (source)"
        if self.chunked:
            name = f"{name} (chunked)"
        return name

    def isAudioOnly(self):
        return self.audioOnly

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.channel}] [{self.resolutionName}]>"

class VideoUrl(TwitchPlaybackObject):
    def __init__(self, videoId, resolutionName, url, data, source, chunked, audioOnly):
        self.videoId = videoId
        self.resolutionName = resolutionName
        self.url = url
        self.data = data
        self.source = source
        self.chunked = chunked
        self.audioOnly = audioOnly

    @property
    def displayName(self):
        name = self.resolutionName
        if self.source:
            name = f"{name} (source)"
        if self.chunked:
            name = f"{name} (chunked)"
        return name

    def isAudioOnly(self):
        return self.audioOnly

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.videoId}] [{self.resolutionName}]>"

class ClipUrl(TwitchPlaybackObject):
    def __init__(self, slug, resolutionName, url):
        self.slug = slug
        self.resolutionName = resolutionName
        self.url = url

    @property
    def displayName(self):
        return self.resolutionName

    def isAudioOnly(self):
        return False

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.slug}] [{self.resolutionName}]>"