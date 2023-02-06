from .QueryParser import TwitchQueryParser
from .ExternalPlaylist import ExternalPlaylistReader

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

    class NoResultsFound(Exception):
        def __str__(self):
            return "No Results Found"


class Search:
    API = TwitchGqlAPI.TwitchGqlAPI()

    @classmethod
    def Query(cls, mode, query, searchExternalContent=False):
        if mode.isUnknown():
            parsedData = TwitchQueryParser.parseQuery(query)
            for mode, query in parsedData:
                try:
                    return cls.Mode(mode, query, searchExternalContent)
                except TwitchGqlAPI.Exceptions.NetworkError:
                    raise Exceptions.NetworkError
                except:
                    pass
            raise Exceptions.NoResultsFound
        elif mode.isUrl():
            mode, query = TwitchQueryParser.parseUrl(query)
        return cls.Mode(mode, query, searchExternalContent)

    @classmethod
    def Mode(cls, mode, query, searchExternalContent=False):
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
        elif mode.isClip():
            try:
                return cls.API.getClip(query)
            except TwitchGqlAPI.Exceptions.DataNotFound:
                raise Exceptions.ClipNotFound
        else:
            if searchExternalContent:
                try:
                    return ExternalPlaylistReader(query).checkUrl()
                except:
                    pass
            raise Exceptions.InvalidURL

    @classmethod
    def Channel(cls, id="", login=""):
        try:
            return cls.API.getChannel(id, login)
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