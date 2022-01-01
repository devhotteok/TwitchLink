from .TwitchPlaybackModels import TwitchPlaybackAccessTokenTypes, StreamUrl, VideoUrl, ClipUrl
from .TwitchPlaylistReader import PlaylistReader
from .TwitchPlaybackConfig import Config

from Services.NetworkRequests import requests

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
            return "Twitch API Error\nstatus_code : {}\n{}".format(self.status_code, self.data)

    class ParseError(Exception):
        def __str__(self):
            return "Failed to read data"

    class TokenError(Exception):
        def __str__(self):
            return "Token Error - Invalid token"

    class ChannelIsOffline(Exception):
        def __init__(self, CHANNEL_NAME):
            self.CHANNEL_NAME = CHANNEL_NAME

        def __str__(self):
            return "Channel Is Offline\nChannel : {}".format(self.CHANNEL_NAME)

    class ChannelNotFound(Exception):
        def __init__(self, CHANNEL_NAME):
            self.CHANNEL_NAME = CHANNEL_NAME

        def __str__(self):
            return "Channel Not Found\nChannel : {}".format(self.CHANNEL_NAME)

    class VideoRestricted(Exception):
        def __init__(self, VIDEO_ID):
            self.VIDEO_ID = VIDEO_ID

        def __str__(self):
            return "Video Restricted - Subscribers Only\nVideo : {}".format(self.VIDEO_ID)

    class VideoNotFound(Exception):
        def __init__(self, VIDEO_ID):
            self.VIDEO_ID = VIDEO_ID

        def __str__(self):
            return "Video Not Found\nVideo : {}".format(self.VIDEO_ID)

    class ClipNotFound(Exception):
        def __init__(self, SLUG):
            self.SLUG = SLUG

        def __str__(self):
            return "Clip Not Found\nClip : {}".format(self.SLUG)

    class InvalidResolution(Exception):
        def __init__(self, resolutions):
            self.resolutions = resolutions

        def __str__(self):
            return "Invalid Resolution\nTry {}".format(self.resolutions)

class TwitchPlaybackAccessToken:
    def __init__(self, tokenType):
        self.type = tokenType
        self.resolutions = {}

    def resolution(self, resolution):
        if resolution in self.resolutions:
            return self.resolutions[resolution]
        else:
            raise Exceptions.InvalidResolution(self.getResolutions())

    def getResolutions(self):
        return list(self.resolutions.keys())

class TwitchStream(TwitchPlaybackAccessToken, PlaylistReader):
    def __init__(self, CHANNEL_NAME, OAUTH_TOKEN=""):
        super().__init__(TwitchPlaybackAccessTokenTypes.STREAM())
        self.CHANNEL_NAME = CHANNEL_NAME
        self.OAUTH_TOKEN = OAUTH_TOKEN
        self.loadStream()

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
                "playerType": "site"
            }
        }
        try:
            response = requests.post(Config.GQL_SERVER, headers={"Client-ID": Config.GQL_CLIENT_ID, "Authorization": "OAuth {}".format(self.OAUTH_TOKEN)}, json=payload)
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            accessToken = response.json()["data"]["streamPlaybackAccessToken"]
            if accessToken == None:
                raise Exceptions.ChannelNotFound(self.CHANNEL_NAME)
            self.sig = accessToken["signature"]
            self.token = accessToken["value"]
            self.hideAds = json.loads(self.token)["hide_ads"]
        elif response.status_code == 401:
            raise Exceptions.TokenError
        else:
            raise Exceptions.TwitchApiError(response)

    def getStreamPlaylist(self):
        try:
            response = requests.get("{}/{}.m3u8".format(Config.HLS_SERVER, self.CHANNEL_NAME), params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token})
        except:
            raise Exceptions.TwitchApiError
        if response.status_code == 200:
            self.playList = response.text
        elif response.status_code == 404:
            raise Exceptions.ChannelIsOffline(self.CHANNEL_NAME)
        else:
            raise Exceptions.TwitchApiError(response)

    def loadStream(self):
        try:
            self.getStreamToken()
            self.getStreamPlaylist()
            self.found = True
        except Exceptions.ChannelNotFound:
            self.playList = None
            self.found = Exceptions.ChannelNotFound
        except Exceptions.ChannelIsOffline:
            self.playList = None
            self.found = Exceptions.ChannelIsOffline
        except:
            raise Exceptions.ParseError
        else:
            self.getStreamUrl()

    def getStreamUrl(self):
        resolutions = {}
        if self.found == True:
            expect = False
            for line in self.playList.split("\n"):
                tag = self.getTag(line)
                if tag != None:
                    if tag.name == "EXT-X-MEDIA":
                        expect = tag.data
                    continue
                if expect != False:
                    name = expect.get("NAME", "")
                    if expect.get("GROUP-ID") == "chunked":
                        name = "{} (chunked)".format(name)
                    resolutions[name] = StreamUrl(self.CHANNEL_NAME, name, line, expect)
                    expect = False
                    continue
            if len(resolutions) == 0:
                self.found = Exceptions.ChannelIsOffline
        self.resolutions = dict(sorted(resolutions.items(), key=lambda item: item[1].data.get("DEFAULT") == "NO"))

class TwitchVideo(TwitchPlaybackAccessToken, PlaylistReader):
    def __init__(self, VIDEO_ID, OAUTH_TOKEN=""):
        super().__init__(TwitchPlaybackAccessTokenTypes.VIDEO())
        self.VIDEO_ID = VIDEO_ID
        self.OAUTH_TOKEN = OAUTH_TOKEN
        self.loadVideo()

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
                "vodID": self.VIDEO_ID,
                "playerType": "site"
            }
        }
        try:
            response = requests.post(Config.GQL_SERVER, headers={"Client-ID": Config.GQL_CLIENT_ID, "Authorization": "OAuth {}".format(self.OAUTH_TOKEN)}, json=payload)
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
            response = requests.get("{}/{}.m3u8".format(Config.VOD_SERVER, self.VIDEO_ID), params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token})
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

    def loadVideo(self):
        try:
            self.getVideoToken()
            self.getVideoPlaylist()
            self.found = True
        except Exceptions.VideoRestricted:
            self.playList = None
            self.found = Exceptions.VideoRestricted
        except Exceptions.VideoNotFound:
            self.playList = None
            self.found = Exceptions.VideoNotFound
        except:
            raise Exceptions.ParseError
        else:
            self.getVideoUrl()

    def getVideoUrl(self):
        resolutions = {}
        if self.found == True:
            expect = False
            for line in self.playList.split("\n"):
                tag = self.getTag(line)
                if tag != None:
                    if tag.name == "EXT-X-MEDIA":
                        expect = tag.data
                    continue
                if expect != False:
                    name = expect.get("NAME", "")
                    if expect.get("GROUP-ID") == "chunked":
                        name = "{} (chunked)".format(name)
                    resolutions[name] = VideoUrl(self.VIDEO_ID, name, line, expect)
                    expect = False
                    continue
            if len(resolutions) == 0:
                self.found = Exceptions.VideoNotFound
        self.resolutions = dict(sorted(resolutions.items(), key=lambda item: item[1].data.get("DEFAULT") == "NO"))

class TwitchClip(TwitchPlaybackAccessToken):
    def __init__(self, SLUG, OAUTH_TOKEN=""):
        super().__init__(TwitchPlaybackAccessTokenTypes.CLIP())
        self.SLUG = SLUG
        self.OAUTH_TOKEN = OAUTH_TOKEN
        self.loadClip()

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
            response = requests.post(Config.GQL_SERVER, headers={"Client-ID": Config.GQL_CLIENT_ID, "Authorization": "OAuth {}".format(self.OAUTH_TOKEN)}, json=payload)
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

    def loadClip(self):
        try:
            self.getClipToken()
            self.found = True
        except Exceptions.ClipNotFound:
            self.found = Exceptions.ClipNotFound
        except:
            raise Exceptions.ParseError

    def setResolutions(self, qualities, sig, token):
        for quality in qualities:
            name = "{quality}p{frameRate}".format(quality=quality["quality"], frameRate=quality["frameRate"])
            self.resolutions[name] = ClipUrl(self.SLUG, name, "{url}?sig={sig}&token={token}".format(url=quality["sourceURL"], sig=sig, token=quote(token)))