from .UrlParser import TwitchUrlParser
from .ExternalPlaylist import ExternalPlaylist

from Core import GlobalExceptions
from Services.Twitch.Gql import TwitchGqlAPI
from Services.Twitch.Playback import TwitchPlaybackAccessTokens


class Exceptions(GlobalExceptions.Exceptions):
    class InvalidURL(Exception):
        def __str__(self):
            return "Invalid URL"

    class ChannelNotFound(Exception):
        def __str__(self):
            return "Channel Not Found"

    class VideoNotFound(Exception):
        def __str__(self):
            return "Video Not Found"

    class ClipNotFound(Exception):
        def __str__(self):
            return "Clip Not Found"


class Search:
    API = TwitchGqlAPI.TwitchGqlAPI()

    @classmethod
    def Query(cls, mode, query, searchExternalContent=False):
        if mode.isUrl():
            parseUrl = TwitchUrlParser(query)
            mode, query = parseUrl.type, parseUrl.data
            if mode == None:
                if searchExternalContent:
                    try:
                        return ExternalPlaylist(query)
                    except:
                        pass
                raise Exceptions.InvalidURL
        if mode.isChannel():
            try:
                return cls.API.getChannel(login=query)
            except TwitchGqlAPI.Exceptions.DataNotFound:
                raise Exceptions.ChannelNotFound
        elif mode.isVideo():
            try:
                return cls.API.getVideo(query)
            except TwitchGqlAPI.Exceptions.DataNotFound:
                raise Exceptions.VideoNotFound
        else:
            try:
                return cls.API.getClip(query)
            except TwitchGqlAPI.Exceptions.DataNotFound:
                raise Exceptions.ClipNotFound

    @classmethod
    def Channel(cls, username):
        try:
            return cls.API.getChannel(login=username)
        except TwitchGqlAPI.Exceptions.DataNotFound:
            raise Exceptions.ChannelNotFound

    @classmethod
    def ChannelVideos(cls, channel, videoType, sort, cursor):
        try:
            return cls.API.getChannelVideos(channel, videoType, sort, cursor=cursor)
        except TwitchGqlAPI.Exceptions.DataNotFound:
            raise Exceptions.ChannelNotFound

    @classmethod
    def ChannelClips(cls, channel, filter, cursor):
        try:
            return cls.API.getChannelClips(channel, filter, cursor=cursor)
        except TwitchGqlAPI.Exceptions.DataNotFound:
            raise Exceptions.ChannelNotFound

    @classmethod
    def StreamAccessToken(cls, login, oAuthToken):
        return TwitchPlaybackAccessTokens.TwitchStream(login, oAuthToken)

    @classmethod
    def VideoAccessToken(cls, videoId, oAuthToken):
        return TwitchPlaybackAccessTokens.TwitchVideo(videoId, oAuthToken)

    @classmethod
    def ClipAccessToken(cls, slug, oAuthToken):
        return TwitchPlaybackAccessTokens.TwitchClip(slug, oAuthToken)