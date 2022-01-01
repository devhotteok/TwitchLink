from Services.NetworkRequests import requests
from Services.Twitch.Playback.TwitchPlaybackAccessTokens import TwitchPlaybackAccessToken, TwitchPlaybackAccessTokenTypes, PlaylistReader


class TwitchPlaylist(TwitchPlaybackAccessToken, PlaylistReader):
    class PlaylistUrl:
        def __init__(self, url):
            self.url = url

    def __init__(self, url):
        super().__init__(TwitchPlaybackAccessTokenTypes.STREAM())
        self.url = url
        self.checkUrl()

    def checkUrl(self):
        try:
            if not self.url.split("?")[0].endswith(".m3u8"):
                raise
            if not (self.url.startswith("http://") or self.url.startswith("https://")):
                self.url = "http://{}".format(self.url)
            response = requests.get(self.url)
            if response.status_code != 200:
                raise
            self.checkPlaylist(response.text)
            self.resolutions = {"unknown": self.PlaylistUrl(self.url)}
            self.found = True
        except:
            self.found = False

    def checkPlaylist(self, playlist):
        hasRequiredTags = {"EXTM3U": False, "EXT-X-TARGETDURATION": False, "EXT-X-ENDLIST": False}
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
            self.type.setType(self.type.TYPES.VIDEO)
        else:
            self.type.setType(self.type.TYPES.STREAM)