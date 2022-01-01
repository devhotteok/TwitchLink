class TwitchPlaybackAccessTokenTypes:
    class TYPES:
        STREAM = "stream"
        VIDEO = "video"
        CLIP = "clip"

    STREAM = lambda: TwitchPlaybackAccessTokenTypes(TwitchPlaybackAccessTokenTypes.TYPES.STREAM)
    VIDEO = lambda: TwitchPlaybackAccessTokenTypes(TwitchPlaybackAccessTokenTypes.TYPES.VIDEO)
    CLIP = lambda: TwitchPlaybackAccessTokenTypes(TwitchPlaybackAccessTokenTypes.TYPES.CLIP)

    def __init__(self, tokenType):
        self.setType(tokenType)

    def setType(self, tokenType):
        self._tokenType = tokenType

    def getType(self):
        return self._tokenType

    def isStream(self):
        return self._tokenType == self.TYPES.STREAM

    def isVideo(self):
        return self._tokenType == self.TYPES.VIDEO

    def isClip(self):
        return self._tokenType == self.TYPES.CLIP

    def toString(self):
        return self.getType()

class StreamUrl:
    def __init__(self, channel, resolution, url, data):
        self.channel = channel
        self.resolution = resolution
        self.url = url
        self.data = data

    def __str__(self):
        return "[{}] {}".format(self.resolution, self.channel)

class VideoUrl:
    def __init__(self, videoId, resolution, url, data):
        self.videoId = videoId
        self.resolution = resolution
        self.url = url
        self.data = data

    def __str__(self):
        return "[{}] {}".format(self.resolution, self.videoId)

class ClipUrl:
    def __init__(self, slug, resolution, url):
        self.slug = slug
        self.resolution = resolution
        self.url = url

    def __str__(self):
        return "[{}] {}".format(self.resolution, self.slug)