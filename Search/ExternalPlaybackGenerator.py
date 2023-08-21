from Core import App
from Core.GlobalExceptions import Exceptions
from Services.Playlist.VariantPlaylistReader import VariantPlaylistReader
from Services.Playlist.Resolution import Resolution
from Services.Playlist.Playlist import Playlist
from Services.Twitch.GQL import TwitchGQLModels
from Services.Twitch.Playback import TwitchPlaybackModels

from PyQt6 import QtCore, QtNetwork


class ExternalPlayback:
    pass


class ExternalStreamPlayback(TwitchPlaybackModels.TwitchStreamPlayback, ExternalPlayback):
    def __init__(self, resolutions: dict[str, Resolution]):
        super().__init__("", TwitchGQLModels.StreamPlaybackAccessToken({}), resolutions)


class ExternalVideoPlayback(TwitchPlaybackModels.TwitchVideoPlayback, ExternalPlayback):
    def __init__(self, resolutions: dict[str, Resolution], totalMilliseconds: int):
        super().__init__("", TwitchGQLModels.VideoPlaybackAccessToken({}), resolutions)
        self.totalMilliseconds = totalMilliseconds

    @property
    def totalSeconds(self) -> float:
        return self.totalMilliseconds / 1000


class ExternalPlaybackGenerator(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, url: QtCore.QUrl, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.url = url
        self._reply: QtNetwork.QNetworkReply | None = None
        self._playlistCheckReply: QtNetwork.QNetworkReply | None = None
        self._resolutions: dict[str, Resolution] | None = None
        self._error: Exception | None = None
        self._data: ExternalPlayback | None = None
        self._checkUrl()

    def _checkUrl(self) -> None:
        self._reply = App.NetworkAccessManager.get(QtNetwork.QNetworkRequest(self.url))
        self._reply.finished.connect(self._replyFinished)

    def _replyFinished(self) -> None:
        if self._reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            text = self._reply.readAll().data().decode()
            self._resolutions = VariantPlaylistReader.loads(text, baseUrl=self._reply.url())
            if len(self._resolutions) == 0:
                try:
                    playlist = Playlist()
                    playlist.loads(text, baseUrl=self._reply.url())
                    resolution = VariantPlaylistReader.generateResolution({"NAME": "Unknown", "GROUP-ID": "Unknown"}, self.url)
                    self._resolutions[resolution.groupId] = resolution
                except Exception as e:
                    self._raiseException(e)
                else:
                    self._createExternalPlayback(playlist)
            else:
                self._playlistCheckReply = App.NetworkAccessManager.get(QtNetwork.QNetworkRequest(list(self._resolutions.values())[0].url))
                self._playlistCheckReply.finished.connect(self._playlistCheckFinished)
        else:
            self._raiseException(Exceptions.NetworkError(self._reply))

    def _playlistCheckFinished(self) -> None:
        if self._playlistCheckReply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            try:
                playlist = Playlist()
                playlist.loads(self._playlistCheckReply.readAll().data().decode(), baseUrl=self._playlistCheckReply.url())
            except Exception as e:
                self._raiseException(e)
            else:
                self._createExternalPlayback(playlist)
        else:
            self._raiseException(Exceptions.NetworkError(self._playlistCheckReply))

    def _createExternalPlayback(self, playlist: Playlist) -> None:
        self._data = ExternalVideoPlayback(self._resolutions, playlist.totalMilliseconds) if playlist.isEndList() else ExternalStreamPlayback(self._resolutions)
        self._setFinished()

    def _setFinished(self) -> None:
        self.finished.emit(self)
        self.deleteLater()

    def _raiseException(self, exception: Exception) -> None:
        self._error = exception
        self._setFinished()

    def getError(self) -> Exception:
        return self._error

    def getData(self) -> ExternalPlayback:
        return self._data