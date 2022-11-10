from Services.NetworkRequests import Network
from Services.Twitch.Playback import TwitchPlaybackAccessTokens
from Services.Twitch.Playback import PlaylistReader


class Exceptions:
    class PlaylistNotFound(Exception):
        def __str__(self):
            return "Playlist Not Found"


class ExternalPlaylistReader(PlaylistReader.PlaylistReader):
    def __init__(self, url):
        super(ExternalPlaylistReader, self).__init__()
        self.url = url

    def checkUrl(self):
        try:
            response = Network.session.get(self.url)
            if response.status_code != 200:
                raise
            return self.getExternalPlaylist(response.text)
        except:
            raise Exceptions.PlaylistNotFound

    def getExternalPlaylist(self, playlist):
        resolutions = self.getPlaylistUrl(playlist, host=self.url)
        if len(resolutions) == 0:
            resolution = self.generateResolution({"NAME": "Unknown", "GROUP-ID": "Unknown"}, self.url)
            resolutions[resolution.groupId] = resolution
            totalMilliSeconds = self.getTotalMilliSeconds(playlist)
        else:
            try:
                response = Network.session.get(list(resolutions.values())[0].url)
                if response.status_code != 200:
                    raise
            except:
                raise Exceptions.PlaylistNotFound
            totalMilliSeconds = self.getTotalMilliSeconds(response.text)
        externalPlaylist = ExternalStreamPlaylist() if totalMilliSeconds == None else ExternalVideoPlaylist(totalMilliSeconds)
        externalPlaylist.resolutions = resolutions
        return externalPlaylist

    def getTotalMilliSeconds(self, playlist):
        hasRequiredTags = {
            "EXTM3U": False,
            "EXT-X-TARGETDURATION": False,
            "EXT-X-ENDLIST": False
        }
        totalMilliSeconds = 0
        for line in playlist.split("\n"):
            tag = self.getTag(line)
            if tag != None:
                if tag.name in hasRequiredTags:
                    hasRequiredTags[tag.name] = True
                if tag.name == "EXTINF":
                    totalMilliSeconds += int(float(tag.data[0]) * 1000)
        if not all(list(hasRequiredTags.values())[0:2]):
            raise
        return totalMilliSeconds if hasRequiredTags["EXT-X-ENDLIST"] else None


class ExternalPlaylist(TwitchPlaybackAccessTokens.TwitchPlaybackAccessToken):
    def __str__(self):
        return f"<{self.__class__.__name__}>"


class ExternalStreamPlaylist(ExternalPlaylist):
    def __init__(self):
        super(ExternalStreamPlaylist, self).__init__(TwitchPlaybackAccessTokens.TwitchPlaybackAccessTokenTypes.STREAM)


class ExternalVideoPlaylist(ExternalPlaylist):
    def __init__(self, totalMilliSeconds):
        super(ExternalVideoPlaylist, self).__init__(TwitchPlaybackAccessTokens.TwitchPlaybackAccessTokenTypes.VIDEO)
        self.totalMilliSeconds = totalMilliSeconds

    @property
    def totalSeconds(self):
        return self.totalMilliSeconds / 1000