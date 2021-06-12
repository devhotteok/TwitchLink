import requests
import re
import json

from urllib.parse import quote


class TwitchApiError(Exception):
    def __init__(self, response):
        self.status_code = response.status_code
        if response.headers["Content-Type"] == "application/json":
            self.data = response.json()
        else:
            self.data = response.text

    def __str__(self):
        return "\nTwitch API Error\nstatus_code : " + str(self.status_code) + "\n" + str(self.data)

class TokenError(Exception):
    def __str__(self):
        return "\nToken Error - Invalid token"

class ChannelIsOffline(Exception):
    def __init__(self, CHANNEL_NAME):
        self.CHANNEL_NAME = CHANNEL_NAME

    def __str__(self):
        return "\nChannel Is Offline\nChannel : " + self.CHANNEL_NAME

class ChannelNotFound(Exception):
    def __init__(self, CHANNEL_NAME):
        self.CHANNEL_NAME = CHANNEL_NAME

    def __str__(self):
        return "\nChannel Not Found\nChannel : " + self.CHANNEL_NAME

class VodRestricted(Exception):
    def __init__(self, VOD_ID):
        self.VOD_ID = VOD_ID

    def __str__(self):
        return "\nVod Restricted - Subscribers Only\nVod : " + self.VOD_ID

class VodNotFound(Exception):
    def __init__(self, VOD_ID):
        self.VOD_ID = VOD_ID

    def __str__(self):
        return "\nVod Not Found\nVod : " + self.VOD_ID

class ClipNotFound(Exception):
    def __init__(self, SLUG):
        self.SLUG = SLUG

    def __str__(self):
        return "\nClip Not Found\nClip : " + self.SLUG

class InvalidResolution(Exception):
    def __init__(self, resolutions):
        self.resolutions = resolutions

    def __str__(self):
        return "\nInvalid Resolution\nTry " + str(self.resolutions)

class StreamUrl:
    def __init__(self, channel, resolution, url):
        self.channel = channel
        self.resolution = resolution
        self.url = url

    def __str__(self):
        return "[" + self.resolution + "] " + self.channel

class VodUrl:
    def __init__(self, vod_id, resolution, url):
        self.vod_id = vod_id
        self.resolution = resolution
        self.url = url

    def __str__(self):
        return "[" + self.resolution + "] " + self.vod_id

class ClipUrl:
    def __init__(self, slug, resolution, url):
        self.slug = slug
        self.resolution = resolution
        self.url = url

    def __str__(self):
        return "[" + self.resolution + "] " + self.slug

class TwitchStream:
    GQL_SERVER = "https://gql.twitch.tv/gql"
    HLS_SERVER = "https://usher.ttvnw.net/api/channel/hls"
    CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"
    RESOLUTIONS = re.compile("#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID=\"(.*)\",NAME=\"(.*)\",AUTOSELECT=.*,DEFAULT=.*")
    dataType = "stream"

    def __init__(self, CHANNEL_NAME, user=None):
        self.CHANNEL_NAME = CHANNEL_NAME
        self.OAUTH_TOKEN = ""
        if user != None:
            if user.token != None:
                self.OAUTH_TOKEN = user.token
        self.reloadStream()

    def getStreamToken(self):
        payload = {
            "operationName": "PlaybackAccessToken",
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "0828119ded1c13477966434e15800ff57ddacf13ba1911c129dc2200705b0712"
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
        response = requests.post(self.GQL_SERVER, headers={"Client-ID": self.CLIENT_ID, "Authorization": "OAuth " + self.OAUTH_TOKEN}, json=payload)
        if response.status_code == 200:
            accessToken = response.json()["data"]["streamPlaybackAccessToken"]
            if accessToken == None:
                raise ChannelNotFound(self.CHANNEL_NAME)
            self.sig = accessToken["signature"]
            self.token = accessToken["value"]
            self.hideAds = json.loads(self.token)["hide_ads"]
        elif response.status_code == 401:
            raise TokenError
        else:
            raise TwitchApiError(response)

    def getStreamPlaylist(self):
        response = requests.get(self.HLS_SERVER + "/" + self.CHANNEL_NAME + ".m3u8", params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token})
        if response.status_code == 200:
            self.playList = response.text
        elif response.status_code == 404:
            raise ChannelIsOffline(self.CHANNEL_NAME)
        else:
            raise TwitchApiError(response)

    def reloadStream(self):
        try:
            self.getStreamToken()
            self.getStreamPlaylist()
            self.found = True
        except ChannelIsOffline:
            self.playList = None
            self.found = ChannelIsOffline
        except ChannelNotFound:
            self.playList = None
            self.found = False
        self.loadStreamUrl()

    def loadStreamUrl(self):
        self.resolutions = {}
        if self.found == True:
            data = self.playList.split("\n")
            index = 0
            while index < len(data):
                line = data[index]
                check = re.search(self.RESOLUTIONS, line)
                if check != None:
                    group_id = check.group(1)
                    name = check.group(2)
                    if group_id == "chunked":
                        name += " (chunked)"
                    index += 2
                    self.resolutions[name] = StreamUrl(self.CHANNEL_NAME, name, data[index])
                index += 1

    def resolution(self, resolution):
        if self.found == ChannelIsOffline:
            raise ChannelIsOffline(self.CHANNEL_NAME)
        elif self.found == False:
            raise ChannelNotFound(self.CHANNEL_NAME)
        elif resolution in self.resolutions:
            return self.resolutions[resolution]
        else:
            raise InvalidResolution(self.getResolutions())

    def getResolutions(self):
        return list(self.resolutions.keys())

class TwitchVod:
    GQL_SERVER = "https://gql.twitch.tv/gql"
    VOD_SERVER = "https://usher.ttvnw.net/vod"
    CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"
    RESOLUTIONS = re.compile("#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID=\"(.*)\",NAME=\"(.*)\",AUTOSELECT=.*,DEFAULT=.*")
    dataType = "video"

    def __init__(self, VOD_ID, user=None):
        self.VOD_ID = VOD_ID
        self.OAUTH_TOKEN = ""
        if user != None:
            if user.token != None:
                self.OAUTH_TOKEN = user.token
        self.reloadVod()

    def getVodToken(self):
        payload = {
            "operationName": "PlaybackAccessToken",
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "0828119ded1c13477966434e15800ff57ddacf13ba1911c129dc2200705b0712"
                }
            },
            "variables": {
                "isLive": False,
                "login": "",
                "isVod": True,
                "vodID": self.VOD_ID,
                "playerType": "site"
            }
        }
        response = requests.post(self.GQL_SERVER, headers={"Client-ID": self.CLIENT_ID, "Authorization": "OAuth " + self.OAUTH_TOKEN}, json=payload)
        if response.status_code == 200:
            accessToken = response.json()["data"]["videoPlaybackAccessToken"]
            self.sig = accessToken["signature"]
            self.token = accessToken["value"]
        elif response.status_code == 401:
            raise TokenError
        else:
            raise TwitchApiError(response)

    def getVodPlaylist(self):
        response = requests.get(self.VOD_SERVER + "/" + self.VOD_ID + ".m3u8", params={"allow_source": True, "allow_audio_only": True, "sig": self.sig, "token": self.token})
        if response.status_code == 200:
            self.playList = response.text
        elif response.status_code == 403:
            raise VodRestricted(self.VOD_ID)
        elif response.status_code == 404:
            raise VodNotFound(self.VOD_ID)
        else:
            raise TwitchApiError(response)

    def reloadVod(self):
        try:
            self.getVodToken()
            self.getVodPlaylist()
            self.found = True
        except VodRestricted:
            self.playList = None
            self.found = VodRestricted
        except VodNotFound:
            self.playList = None
            self.found = False
        self.loadVodUrl()

    def loadVodUrl(self):
        self.resolutions = {}
        if self.found == True:
            data = self.playList.split("\n")
            index = 0
            while index < len(data):
                line = data[index]
                check = re.search(self.RESOLUTIONS, line)
                if check != None:
                    group_id = check.group(1)
                    name = check.group(2)
                    if group_id == "chunked":
                        name += " (chunked)"
                    index += 2
                    self.resolutions[name] = VodUrl(self.VOD_ID, name, data[index])
                index += 1

    def resolution(self, resolution):
        if self.found == VodRestricted:
            raise VodRestricted(self.VOD_ID)
        elif self.found == False:
            raise VodNotFound(self.VOD_ID)
        elif resolution in self.resolutions:
            return self.resolutions[resolution]
        else:
            raise InvalidResolution(self.getResolutions())

    def getResolutions(self):
        return list(self.resolutions.keys())

class TwitchClip:
    GQL_SERVER = "https://gql.twitch.tv/gql"
    CLIP_SERVER = "https://usher.ttvnw.net/vod"
    CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"
    dataType = "clip"

    def __init__(self, SLUG, user=None):
        self.SLUG = SLUG
        self.OAUTH_TOKEN = ""
        if user != None:
            if user.token != None:
                self.OAUTH_TOKEN = user.token
        self.reloadClip()

    def getClipToken(self):
        payload = {
            "operationName": "VideoAccessToken_Clip",
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "36b89d2507fce29e5ca551df756d27c1cfe079e2609642b4390aa4c35796eb11"
                }
            },
            "variables": {
                "slug": self.SLUG
            }
        }
        response = requests.post(self.GQL_SERVER, headers={"Client-ID": self.CLIENT_ID, "Authorization": "OAuth " + self.OAUTH_TOKEN}, json=payload)
        if response.status_code == 200:
            clip = response.json()["data"]["clip"]
            if clip == None:
                raise ClipNotFound(self.SLUG)
            accessToken = clip["playbackAccessToken"]
            sig = accessToken["signature"]
            token = accessToken["value"]
            self.id = clip["id"]
            self.setResolutions(clip["videoQualities"], sig, token)
            self.found = True
        elif response.status_code == 401:
            raise TokenError
        else:
            raise TwitchApiError(response)

    def reloadClip(self):
        try:
            self.getClipToken()
            self.found = True
        except ClipNotFound:
            self.resolutions = {}
            self.found = False

    def setResolutions(self, qualities, sig, token):
        self.resolutions = {}
        for quality in qualities:
            name = "{quality}p{frameRate}".format(quality=quality["quality"], frameRate=quality["frameRate"])
            self.resolutions[name] = ClipUrl(self.SLUG, name, "{url}?sig={sig}&token={token}".format(url=quality["sourceURL"], sig=sig, token=quote(token)))

    def resolution(self, resolution):
        if self.found == False:
            raise ClipNotFound(self.SLUG)
        elif resolution in self.resolutions:
            return self.resolutions[resolution]
        else:
            raise InvalidResolution(self.getResolutions())

    def getResolutions(self):
        return list(self.resolutions.keys())