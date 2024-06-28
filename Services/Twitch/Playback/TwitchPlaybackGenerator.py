from . import TwitchPlaybackModels
from .TwitchPlaybackConfig import Config

from Core import App
from Core import GlobalExceptions
from Services.Twitch.GQL import TwitchGQLAPI
from Services.Twitch.GQL import TwitchGQLModels
from Services.Playlist.VariantPlaylistReader import VariantPlaylistReader
from Services.Playlist.Resolution import Resolution

from PyQt6 import QtCore, QtNetwork

import json

from urllib.parse import quote


class Exceptions(GlobalExceptions.Exceptions):
    class Forbidden(Exception):
        def __init__(self, reason: str | None):
            self.reason = reason

        def __str__(self):
            return f"Unavailable Content\nReason: {self.reason}"

    class GeoBlock(Exception):
        def __init__(self, reason: str | None):
            self.reason = reason

        def __str__(self):
            return f"Blocked Content\nReason: {self.reason}"

    class ChannelIsOffline(Exception):
        def __init__(self, login: str):
            self.login = login

        def __str__(self):
            return f"Channel Is Offline\nChannel: {self.login}"

    class ChannelNotFound(Exception):
        def __init__(self, login: str):
            self.login = login

        def __str__(self):
            return f"Channel Not Found\nChannel: {self.login}"

    class StreamRestricted(Exception):
        def __init__(self, login: str):
            self.login = login

        def __str__(self):
            return f"Stream Restricted - Subscriber-Only\nChannel: {self.login}"

    class VideoRestricted(Exception):
        def __init__(self, id: str):
            self.id = id

        def __str__(self):
            return f"Video Restricted - Subscriber-Only\nVideo: {self.id}"

    class VideoNotFound(Exception):
        def __init__(self, id: str):
            self.id = id

        def __str__(self):
            return f"Video Not Found\nVideo: {self.id}"

    class ClipNotFound(Exception):
        def __init__(self, slug: str):
            self.slug = slug

        def __str__(self):
            return f"Clip Not Found\nClip: {self.slug}"


class TwitchStreamPlaybackGenerator(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, login: str, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.login = login
        self.token: TwitchGQLModels.StreamPlaybackAccessToken | None = None
        self._reply: QtNetwork.QNetworkReply | None = None
        self._error: Exception | None = None
        self._data: TwitchPlaybackModels.TwitchStreamPlayback | None = None
        App.TwitchGQL.getStreamPlaybackAccessToken(self.login).finished.connect(self._streamPlaybackAccessTokenHandler)

    def _streamPlaybackAccessTokenHandler(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            self.token = response.getData()
            try:
                self._validateToken()
            except Exception as e:
                self._raiseException(e)
            else:
                self._getStreamPlayback()
        elif isinstance(response.getError(), TwitchGQLAPI.Exceptions.DataNotFound):
            self._raiseException(Exceptions.ChannelNotFound(self.login))
        else:
            self._raiseException(response.getError())

    def _validateToken(self) -> None:
        if self.token.forbidden:
            if self.token.getForbiddenReason() == "UNAUTHORIZED_ENTITLMENTS":
                raise Exceptions.StreamRestricted(self.login)
            else:
                raise Exceptions.Forbidden(self.token.getForbiddenReason())
        if self.token.geoBlock:
            raise Exceptions.GeoBlock(self.token.getGeoBlockReason())

    def _getStreamPlayback(self) -> None:
        params = {"allow_source": True, "allow_audio_only": True, "sig": self.token.signature, "token": self.token.value, "fast_bread": True}
        url = QtCore.QUrl(f"{Config.HLS_SERVER}{self.login}.m3u8")
        query = QtCore.QUrlQuery()
        for key, value in params.items():
            query.addQueryItem(key, value if isinstance(value, str) else json.dumps(value))
        url.setQuery(query)
        request = QtNetwork.QNetworkRequest(url)
        self._reply = App.NetworkAccessManager.get(request)
        self._reply.finished.connect(self._replyFinished)

    def _replyFinished(self) -> None:
        if self._reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            resolutions = VariantPlaylistReader.loads(self._reply.readAll().data().decode(errors="ignore"), baseUrl=self._reply.url())
            if len(resolutions) == 0:
                self._raiseException(Exceptions.ChannelIsOffline(self.login))
            else:
                self._data = TwitchPlaybackModels.TwitchStreamPlayback(
                    login=self.login,
                    token=self.token,
                    resolutions=resolutions
                )
                self._setFinished()
        elif self._reply.error() == QtNetwork.QNetworkReply.NetworkError.ContentNotFoundError:
            self._raiseException(Exceptions.ChannelIsOffline(self.login))
        else:
            self._raiseException(Exceptions.NetworkError(self._reply))

    def _setFinished(self) -> None:
        self.finished.emit(self)
        self.deleteLater()

    def _raiseException(self, exception: Exception) -> None:
        self._error = exception
        self._setFinished()

    def getError(self) -> Exception | None:
        return self._error

    def getData(self) -> TwitchPlaybackModels.TwitchStreamPlayback | None:
        return self._data


class TwitchVideoPlaybackGenerator(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, id: str, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.id = id
        self.token: TwitchGQLModels.VideoPlaybackAccessToken | None = None
        self._reply: QtNetwork.QNetworkReply | None = None
        self._error: Exception | None = None
        self._data: TwitchPlaybackModels.TwitchVideoPlayback | None = None
        App.TwitchGQL.getVideoPlaybackAccessToken(self.id).finished.connect(self._videoPlaybackAccessTokenHandler)

    def _videoPlaybackAccessTokenHandler(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            self.token = response.getData()
            self._getVideoPlayback()
        elif isinstance(response.getError(), TwitchGQLAPI.Exceptions.DataNotFound):
            self._raiseException(Exceptions.VideoNotFound(self.id))
        else:
            self._raiseException(response.getError())

    def _getVideoPlayback(self) -> None:
        params = {"allow_source": True, "allow_audio_only": True, "sig": self.token.signature, "token": self.token.value}
        url = QtCore.QUrl(f"{Config.VOD_SERVER}{self.id}.m3u8")
        query = QtCore.QUrlQuery()
        for key, value in params.items():
            query.addQueryItem(key, value if isinstance(value, str) else json.dumps(value))
        url.setQuery(query)
        request = QtNetwork.QNetworkRequest(url)
        self._reply = App.NetworkAccessManager.get(request)
        self._reply.finished.connect(self._replyFinished)

    def _replyFinished(self) -> None:
        if self._reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            resolutions = VariantPlaylistReader.loads(self._reply.readAll().data().decode(errors="ignore"), baseUrl=self._reply.url())
            if len(resolutions) == 0:
                self._raiseException(Exceptions.VideoNotFound(self.id))
            else:
                self._data = TwitchPlaybackModels.TwitchVideoPlayback(
                    id=self.id,
                    token=self.token,
                    resolutions=resolutions
                )
                self._setFinished()
        elif self._reply.error() == QtNetwork.QNetworkReply.NetworkError.ContentAccessDenied:
            self._raiseException(Exceptions.VideoRestricted(self.id))
        elif self._reply.error() == QtNetwork.QNetworkReply.NetworkError.ContentNotFoundError:
            self._raiseException(Exceptions.VideoNotFound(self.id))
        else:
            self._raiseException(Exceptions.NetworkError(self._reply))

    def _setFinished(self) -> None:
        self.finished.emit(self)
        self.deleteLater()

    def _raiseException(self, exception: Exception) -> None:
        self._error = exception
        self._setFinished()

    def getError(self) -> Exception | None:
        return self._error

    def getData(self) -> TwitchPlaybackModels.TwitchVideoPlayback | None:
        return self._data


class TwitchClipPlaybackGenerator(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, slug: str, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.slug = slug
        self.token: TwitchGQLModels.ClipPlaybackAccessToken | None = None
        self._error: Exception | None = None
        self._data: TwitchPlaybackModels.TwitchClipPlayback | None = None
        App.TwitchGQL.getClipPlaybackAccessToken(self.slug).finished.connect(self._clipPlaybackAccessTokenHandler)

    def _clipPlaybackAccessTokenHandler(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            self.token = response.getData()
            self._getClipPlayback()
        elif isinstance(response.getError(), TwitchGQLAPI.Exceptions.DataNotFound):
            self._raiseException(Exceptions.ClipNotFound(self.slug))
        else:
            self._raiseException(response.getError())

    def _getClipPlayback(self) -> None:
        resolutions = []
        for quality in self.token.videoQualities:
            resolutions.append(
                Resolution(
                    name=f"{quality['quality']}p{quality['frameRate']}",
                    groupId=f"{quality['quality']}p{quality['frameRate']}",
                    url=QtCore.QUrl(f"{quality['sourceURL']}?sig={self.token.signature}&token={quote(self.token.value)}")
                )
            )
        if len(resolutions) == 0:
            self._raiseException(Exceptions.ClipNotFound(self.slug))
        else:
            self._data = TwitchPlaybackModels.TwitchClipPlayback(
                slug=self.slug,
                token=self.token,
                resolutions={resolution.groupId: resolution for resolution in sorted(resolutions, reverse=True)}
            )
            self._setFinished()

    def _setFinished(self) -> None:
        self.finished.emit(self)
        self.deleteLater()

    def _raiseException(self, exception: Exception) -> None:
        self._error = exception
        self._setFinished()

    def getError(self) -> Exception | None:
        return self._error

    def getData(self) -> TwitchPlaybackModels.TwitchClipPlayback | None:
        return self._data