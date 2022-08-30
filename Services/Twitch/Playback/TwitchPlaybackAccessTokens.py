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

class ResolutionNameGenerator:
    def generateResolutionName(self, name):
        nameCheck = name.lower()
        for key in [" ", "-", "_"]:
            nameCheck = nameCheck.replace(key, "")
        if "source" in nameCheck:
            isSource = True
        else:
            isSource = False
        if "audioonly" in nameCheck:
            isAudioOnly = True
            name = Config.AUDIO_ONLY_RESOLUTION_NAME
        else:
            isAudioOnly = False
        return self.removeBrackets(name), isSource, isAudioOnly

    def removeBrackets(self, name):
        newName = ""
        brackets = 0
        for char in name:
            if char == "(":
                brackets += 1
                continue
            elif char == ")":
                brackets -= 1
                continue
            if brackets == 0:
                newName += char
            elif brackets < 0:
                return name
        if brackets == 0:
            return " ".join(newName.split())
        else:
            return name


class TwitchStream(TwitchPlaybackAccessToken, PlaylistReader, ResolutionNameGenerator):
    def __init__(self, CHANNEL_NAME, OAUTH_TOKEN=""):
        super(TwitchStream, self).__init__(TwitchPlaybackAccessTokenTypes.STREAM)
        self.CHANNEL_NAME = CHANNEL_NAME
        self.OAUTH_TOKEN = OAUTH_TOKEN
        self.loadStream()

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
            response = Network.session.get(f"{Config.HLS_SERVER}/{self.CHANNEL_NAME}.m3u8", params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token, "fast_bread": True})
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            self.playList = response.text
        elif response.status_code == 404:
            raise Exceptions.ChannelIsOffline(self.CHANNEL_NAME)
        else:
            raise Exceptions.TwitchApiError(response)

    def getStreamUrl(self):
        resolutions = {}
        expect = False
        for line in self.playList.split("\n"):
            tag = self.getTag(line)
            if tag != None:
                if tag.name == "EXT-X-MEDIA":
                    expect = tag.data
                continue
            if expect != False:
                name, isSource, isAudioOnly = self.generateResolutionName(expect.get("NAME", ""))
                isChunked = expect.get("GROUP-ID") == "chunked"
                resolutions[name] = StreamUrl(self.CHANNEL_NAME, name, line, expect, isSource, isChunked, isAudioOnly)
                expect = False
                continue
        if len(resolutions) == 0:
            raise Exceptions.ChannelIsOffline
        self.resolutions = dict(sorted(resolutions.items(), key=lambda item: item[1].data.get("DEFAULT") == "NO"))

class TwitchVideo(TwitchPlaybackAccessToken, PlaylistReader, ResolutionNameGenerator):
    def __init__(self, VIDEO_ID, OAUTH_TOKEN=""):
        super(TwitchVideo, self).__init__(TwitchPlaybackAccessTokenTypes.VIDEO)
        self.VIDEO_ID = VIDEO_ID
        self.OAUTH_TOKEN = OAUTH_TOKEN
        self.loadVideo()

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
            response = Network.session.get(f"{Config.VOD_SERVER}/{self.VIDEO_ID}.m3u8", params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token})
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            self.playList = response.text
        elif response.status_code == 403:
            raise Exceptions.VideoRestricted(self.VIDEO_ID)
        elif response.status_code == 404:
            raise Exceptions.VideoNotFound(self.VIDEO_ID)
        else:
            raise Exceptions.TwitchApiError(response)

    def getVideoUrl(self):
        resolutions = {}
        expect = False
        for line in self.playList.split("\n"):
            tag = self.getTag(line)
            if tag != None:
                if tag.name == "EXT-X-MEDIA":
                    expect = tag.data
                continue
            if expect != False:
                name, isSource, isAudioOnly = self.generateResolutionName(expect.get("NAME", ""))
                isChunked = expect.get("GROUP-ID") == "chunked"
                resolutions[name] = VideoUrl(self.VIDEO_ID, name, line, expect, isSource, isChunked, isAudioOnly)
                expect = False
                continue
        if len(resolutions) == 0:
            raise Exceptions.VideoNotFound
        self.resolutions = dict(sorted(resolutions.items(), key=lambda item: item[1].data.get("DEFAULT") == "NO"))

class TwitchClip(TwitchPlaybackAccessToken):
    def __init__(self, SLUG, OAUTH_TOKEN=""):
        super(TwitchClip, self).__init__(TwitchPlaybackAccessTokenTypes.CLIP)
        self.SLUG = SLUG
        self.OAUTH_TOKEN = OAUTH_TOKEN
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
            self.setResolutions(clip["videoQualities"], sig, token)
            if len(self.resolutions) == 0:
                raise Exceptions.ClipNotFound(self.SLUG)
        elif response.status_code == 401:
            raise Exceptions.TokenError
        else:
            raise Exceptions.TwitchApiError(response)

    def setResolutions(self, qualities, sig, token):
        for quality in qualities:
            name = f"{quality['quality']}p{quality['frameRate']}"
            self.resolutions[name] = ClipUrl(self.SLUG, name, f"{quality['sourceURL']}?sig={sig}&token={quote(token)}")