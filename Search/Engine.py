from .UrlParser import TwitchUrlParser
from .PlaylistAccessToken import TwitchPlaylist

from Core import GlobalExceptions
from Services.Utils.WorkerThreads import WorkerThread
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
    def Query(cls, mode, query):
        if mode.isUrl():
            parseUrl = TwitchUrlParser(query)
            mode, query = parseUrl.type, parseUrl.data
            if mode == None:
                playlist = TwitchPlaylist(query)
                if playlist.found:
                    return playlist
                else:
                    raise Exceptions.InvalidURL
        if mode.isChannel():
            try:
                return cls.API.getChannel(login=query)
            except Exception as e:
                if type(e) == TwitchGqlAPI.Exceptions.DataNotFound:
                    raise Exceptions.ChannelNotFound
                else:
                    raise Exceptions.NetworkError
        elif mode.isVideo():
            try:
                return cls.API.getVideo(query)
            except Exception as e:
                if type(e) == TwitchGqlAPI.Exceptions.DataNotFound:
                    raise Exceptions.VideoNotFound
                else:
                    raise Exceptions.NetworkError
        else:
            try:
                return cls.API.getClip(query)
            except Exception as e:
                if type(e) == TwitchGqlAPI.Exceptions.DataNotFound:
                    raise Exceptions.ClipNotFound
                else:
                    raise Exceptions.NetworkError

    @classmethod
    def Channel(cls, username):
        try:
            return cls.API.getChannel(login=username)
        except TwitchGqlAPI.Exceptions.DataNotFound:
            raise Exceptions.ChannelNotFound
        except:
            raise Exceptions.NetworkError

    @classmethod
    def ChannelVideos(cls, channel, videoType, sort, cursor):
        try:
            return cls.API.getChannelVideos(channel, videoType, sort, cursor=cursor)
        except TwitchGqlAPI.Exceptions.DataNotFound:
            raise Exceptions.ChannelNotFound
        except:
            raise Exceptions.NetworkError

    @classmethod
    def ChannelClips(cls, channel, filter, cursor):
        try:
            return cls.API.getChannelClips(channel, filter, cursor=cursor)
        except TwitchGqlAPI.Exceptions.DataNotFound:
            raise Exceptions.ChannelNotFound
        except:
            raise Exceptions.NetworkError

    @classmethod
    def StreamAccessToken(cls, login, oAuthToken):
        try:
            return TwitchPlaybackAccessTokens.TwitchStream(login, oAuthToken)
        except TwitchPlaybackAccessTokens.Exceptions.TokenError:
            raise TwitchPlaybackAccessTokens.Exceptions.TokenError
        except:
            raise Exceptions.NetworkError

    @classmethod
    def VideoAccessToken(cls, videoId, oAuthToken):
        try:
            return TwitchPlaybackAccessTokens.TwitchVideo(videoId, oAuthToken)
        except TwitchPlaybackAccessTokens.Exceptions.TokenError:
            raise TwitchPlaybackAccessTokens.Exceptions.TokenError
        except:
            raise Exceptions.NetworkError

    @classmethod
    def ClipAccessToken(cls, slug, oAuthToken):
        try:
            return TwitchPlaybackAccessTokens.TwitchClip(slug, oAuthToken)
        except TwitchPlaybackAccessTokens.Exceptions.TokenError:
            raise TwitchPlaybackAccessTokens.Exceptions.TokenError
        except:
            raise Exceptions.NetworkError


class SearchThread(WorkerThread):
    def __init__(self, target, callback, args=None, kwargs=None):
        super().__init__(target, args, kwargs)
        self.resultSignal.connect(callback)
        self.start()