from Services.NetworkRequests import Network
from Services.Twitch.Playback import TwitchPlaybackAccessTokens


class Exceptions:
    class PlaylistNotFound(Exception):
        def __str__(self):
            return "Playlist Not Found"


class ExternalPlaylist(TwitchPlaybackAccessTokens.TwitchPlaybackAccessToken, TwitchPlaybackAccessTokens.PlaylistReader):
    def __init__(self, url):
        super(ExternalPlaylist, self).__init__(TwitchPlaybackAccessTokens.TwitchPlaybackAccessTokenTypes.STREAM)
        self.url = url
        self.checkUrl()

    def checkUrl(self):
        try:
            response = Network.session.get(self.url)
            if response.status_code != 200:
                raise
            self.checkPlaylist(response.text)
            if self.type.isStream():
                url = TwitchPlaybackAccessTokens.StreamUrl("", "Unknown", self.url, None, False, False, False)
                audioOnlyUrl = TwitchPlaybackAccessTokens.StreamUrl("", TwitchPlaybackAccessTokens.Config.AUDIO_ONLY_RESOLUTION_NAME, self.url, None, False, False, True)
            else:
                url = TwitchPlaybackAccessTokens.VideoUrl(None, "Unknown", self.url, None, False, False, False)
                audioOnlyUrl = TwitchPlaybackAccessTokens.VideoUrl(None, TwitchPlaybackAccessTokens.Config.AUDIO_ONLY_RESOLUTION_NAME, self.url, None, False, False, True)
            self.resolutions = {url.resolutionName: url, audioOnlyUrl.resolutionName: audioOnlyUrl}
        except:
            raise Exceptions.PlaylistNotFound

    def checkPlaylist(self, playlist):
        hasRequiredTags = {
            "EXTM3U": False,
            "EXT-X-TARGETDURATION": False,
            "EXT-X-ENDLIST": False
        }
        totalSeconds = 0.0
        for line in playlist.split("\n"):
            tag = self.getTag(line)
            if tag != None:
                if tag.name in hasRequiredTags:
                    hasRequiredTags[tag.name] = True
                if tag.name == "EXTINF":
                    totalSeconds += float(tag.data[0])
        if not all(list(hasRequiredTags.values())[0:2]):
            raise
        if hasRequiredTags["EXT-X-ENDLIST"]:
            self.totalSeconds = totalSeconds
            self.type.setType(self.type.VIDEO)
        else:
            self.type.setType(self.type.STREAM)