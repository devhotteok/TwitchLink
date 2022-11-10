from .TwitchPlaybackModels import TwitchPlaybackAccessTokenTypes, StreamUrl, VideoUrl, ClipUrl
from .PlaylistReader import PlaylistReader
from .TwitchPlaybackConfig import Config

from Services.NetworkRequests import Network
from Database.EncoderDecoder import Codable

import json

from urllib.parse import quote


class Exceptions:
    class TwitchApiError(Exception):
        def __init__(self, response=None):
            if response == None:
                self.status_code = None
                self.data = "Unable to connect to server"
            else:
                self.status_code = response.status_code
                self.data = response.getData()

        def __str__(self):
            return f"Twitch API Error\nstatus_code: {self.status_code}\n{self.data}"

    class TokenError(Exception):
        def __str__(self):
            return "Token Error - Invalid token"

    class Forbidden(Exception):
        def __init__(self, reason):
            self.reason = reason

        def __str__(self):
            return f"Unavailable Content\nReason: {self.reason}"

    class GeoBlock(Exception):
        def __init__(self, reason):
            self.reason = reason

        def __str__(self):
            return f"Blocked Content\nReason: {self.reason}"

    class ChannelIsOffline(Exception):
        def __init__(self, CHANNEL_NAME):
            self.CHANNEL_NAME = CHANNEL_NAME

        def __str__(self):
            return f"Channel Is Offline\nChannel: {self.CHANNEL_NAME}"

    class ChannelNotFound(Exception):
        def __init__(self, CHANNEL_NAME):
            self.CHANNEL_NAME = CHANNEL_NAME

        def __str__(self):
            return f"Channel Not Found\nChannel: {self.CHANNEL_NAME}"

    class VideoRestricted(Exception):
        def __init__(self, VIDEO_ID):
            self.VIDEO_ID = VIDEO_ID

        def __str__(self):
            return f"Video Restricted - Subscriber-Only\nVideo: {self.VIDEO_ID}"

    class VideoNotFound(Exception):
        def __init__(self, VIDEO_ID):
            self.VIDEO_ID = VIDEO_ID

        def __str__(self):
            return f"Video Not Found\nVideo: {self.VIDEO_ID}"

    class ClipNotFound(Exception):
        def __init__(self, SLUG):
            self.SLUG = SLUG

        def __str__(self):
            return f"Clip Not Found\nClip: {self.SLUG}"

    class InvalidResolution(Exception):
        def __init__(self, resolutions):
            self.resolutions = resolutions

        def __str__(self):
            return f"Invalid Resolution\nTry {self.resolutions}"

class TwitchPlaybackAccessToken(Codable):
    CODABLE_INIT_MODEL = False
    CODABLE_STRICT_MODE = False

    def __init__(self, tokenType):
        self.type = TwitchPlaybackAccessTokenTypes(tokenType)
        self.resolutions = {}

    def resolution(self, resolution):
        if resolution in self.resolutions:
            return self.resolutions[resolution]
        else:
            raise Exceptions.InvalidResolution(self.getResolutionKeys())

    def getResolutionKeys(self):
        return list(self.resolutions.keys())

    def getResolutions(self):
        return list(self.resolutions.values())


class TwitchStream(TwitchPlaybackAccessToken, PlaylistReader):
    def __init__(self, CHANNEL_NAME, OAUTH_TOKEN=""):
        super(TwitchStream, self).__init__(TwitchPlaybackAccessTokenTypes.STREAM)
        self.CHANNEL_NAME = CHANNEL_NAME
        self.OAUTH_TOKEN = OAUTH_TOKEN
        if self.CHANNEL_NAME != None:
            self.loadStream()

    @property
    def PLAYLIST_HOST_URL(self):
        return f"{Config.HLS_SERVER}/{self.CHANNEL_NAME}.m3u8"

    def loadStream(self):
        self.getStreamToken()
        self.getStreamPlaylist()
        self.getStreamUrl()

    def getStreamToken(self):
        payload = {
            "operationName": Config.STREAM_TOKEN_OPERATOR[0],
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": Config.STREAM_TOKEN_OPERATOR[1]
                }
            },
            "variables": {
                "isLive": True,
                "login": self.CHANNEL_NAME,
                "isVod": False,
                "vodID": "",
                "playerType": "embed"
            }
        }
        try:
            response = Network.session.post(Config.GQL_SERVER, headers={"Client-ID": Config.GQL_CLIENT_ID, "Authorization": f"OAuth {self.OAUTH_TOKEN}"}, json=payload)
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            accessToken = response.json()["data"]["streamPlaybackAccessToken"]
            if accessToken == None:
                raise Exceptions.ChannelNotFound(self.CHANNEL_NAME)
            self.sig = accessToken["signature"]
            self.token = accessToken["value"]
            tokenData = json.loads(self.token)
            self.hideAds = tokenData["hide_ads"]
            self.forbidden = tokenData["authorization"]["reason"] if tokenData["authorization"]["forbidden"] else False
            self.geoBlock = tokenData["geoblock_reason"] if tokenData["ci_gb"] else False
            if self.forbidden:
                raise Exceptions.Forbidden(self.forbidden)
            if self.geoBlock:
                raise Exceptions.GeoBlock(self.geoBlock)
        elif response.status_code == 401:
            raise Exceptions.TokenError
        else:
            raise Exceptions.TwitchApiError(response)

    def getStreamPlaylist(self):
        try:
            response = Network.session.get(self.PLAYLIST_HOST_URL, params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token, "fast_bread": True})
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            self.playlist = response.text
        elif response.status_code == 404:
            raise Exceptions.ChannelIsOffline(self.CHANNEL_NAME)
        else:
            raise Exceptions.TwitchApiError(response)

    def getStreamUrl(self):
        self.resolutions = self.getPlaylistUrl(self.playlist, host=self.PLAYLIST_HOST_URL)
        if len(self.resolutions) == 0:
            raise Exceptions.ChannelIsOffline

    def generateResolution(self, data, url):
        return StreamUrl(
            channel=self.CHANNEL_NAME,
            name=data.get("NAME", ""),
            groupId=data.get("GROUP-ID", ""),
            url=url,
            autoSelect=data.get("AUTOSELECT", "") == "YES",
            default=data.get("DEFAULT", "") == "YES"
        )


class TwitchVideo(TwitchPlaybackAccessToken, PlaylistReader):
    def __init__(self, VIDEO_ID, OAUTH_TOKEN=""):
        super(TwitchVideo, self).__init__(TwitchPlaybackAccessTokenTypes.VIDEO)
        self.VIDEO_ID = VIDEO_ID
        self.OAUTH_TOKEN = OAUTH_TOKEN
        if self.VIDEO_ID != None:
            self.loadVideo()

    @property
    def PLAYLIST_HOST_URL(self):
        return f"{Config.VOD_SERVER}/{self.VIDEO_ID}.m3u8"

    def loadVideo(self):
        self.getVideoToken()
        self.getVideoPlaylist()
        self.getVideoUrl()

    def getVideoToken(self):
        payload = {
            "operationName": Config.VIDEO_TOKEN_OPERATOR[0],
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": Config.VIDEO_TOKEN_OPERATOR[1]
                }
            },
            "variables": {
                "isLive": False,
                "login": "",
                "isVod": True,
                "vodID": str(self.VIDEO_ID),
                "playerType": "embed"
            }
        }
        try:
            response = Network.session.post(Config.GQL_SERVER, headers={"Client-ID": Config.GQL_CLIENT_ID, "Authorization": f"OAuth {self.OAUTH_TOKEN}"}, json=payload)
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            accessToken = response.json()["data"]["videoPlaybackAccessToken"]
            if accessToken == None:
                raise Exceptions.VideoNotFound(self.VIDEO_ID)
            self.sig = accessToken["signature"]
            self.token = accessToken["value"]
        elif response.status_code == 401:
            raise Exceptions.TokenError
        else:
            raise Exceptions.TwitchApiError(response)

    def getVideoPlaylist(self):
        try:
            response = Network.session.get(self.PLAYLIST_HOST_URL, params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token})
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            self.playlist = response.text
        elif response.status_code == 403:
            raise Exceptions.VideoRestricted(self.VIDEO_ID)
        elif response.status_code == 404:
            raise Exceptions.VideoNotFound(self.VIDEO_ID)
        else:
            raise Exceptions.TwitchApiError(response)

    def getVideoUrl(self):
        self.resolutions = self.getPlaylistUrl(self.playlist, host=self.PLAYLIST_HOST_URL)
        if len(self.resolutions) == 0:
            raise Exceptions.VideoNotFound

    def generateResolution(self, data, url):
        return VideoUrl(
            videoId=self.VIDEO_ID,
            name=data.get("NAME", ""),
            groupId=data.get("GROUP-ID", ""),
            url=url,
            autoSelect=data.get("AUTOSELECT", "") == "YES",
            default=data.get("DEFAULT", "") == "YES"
        )

class TwitchClip(TwitchPlaybackAccessToken):
    def __init__(self, SLUG, OAUTH_TOKEN=""):
        super(TwitchClip, self).__init__(TwitchPlaybackAccessTokenTypes.CLIP)
        self.SLUG = SLUG
        self.OAUTH_TOKEN = OAUTH_TOKEN
        if self.SLUG != None:
            self.loadClip()

    def loadClip(self):
        self.getClipToken()

    def getClipToken(self):
        payload = {
            "operationName": Config.CLIP_TOKEN_OPERATOR[0],
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": Config.CLIP_TOKEN_OPERATOR[1]
                }
            },
            "variables": {
                "slug": self.SLUG
            }
        }
        try:
            response = Network.session.post(Config.GQL_SERVER, headers={"Client-ID": Config.GQL_CLIENT_ID, "Authorization": f"OAuth {self.OAUTH_TOKEN}"}, json=payload)
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            clip = response.json()["data"]["clip"]
            if clip == None:
                raise Exceptions.ClipNotFound(self.SLUG)
            accessToken = clip["playbackAccessToken"]
            sig = accessToken["signature"]
            token = accessToken["value"]
            self.id = clip["id"]
            self.getClipUrl(clip["videoQualities"], sig, token)
            if len(self.resolutions) == 0:
                raise Exceptions.ClipNotFound(self.SLUG)
        elif response.status_code == 401:
            raise Exceptions.TokenError
        else:
            raise Exceptions.TwitchApiError(response)

    def getClipUrl(self, qualities, sig, token):
        resolutions = {}
        for quality in qualities:
            resolution = ClipUrl(
                slug=self.SLUG,
                name=f"{quality['quality']}p{quality['frameRate']}",
                url=f"{quality['sourceURL']}?sig={sig}&token={quote(token)}"
            )
            resolutions[resolution.groupId] = resolution
        self.resolutions = dict(sorted(resolutions.items(), key=lambda item: (item[1].frameRate or 0, item[1].quality or 0), reverse=True))