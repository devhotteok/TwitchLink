from Core.GlobalExceptions import Exceptions
from Services.Playlist import Playlist
from Services.Playlist.Segment import Segment

from PyQt6 import QtCore, QtNetwork

import typing


class PlaylistManager(QtCore.QObject):
    playlistUpdated = QtCore.pyqtSignal()
    errorOccurred = QtCore.pyqtSignal(Exception)

    def __init__(self, networkAccessManager: QtNetwork.QNetworkAccessManager, url: QtCore.QUrl, timeout: int = 10000, maxRetryCount: int = 2, retryInterval: int = 1000, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.url = url
        self.playlist = Playlist.Playlist()
        self._range = (None, None)
        self._networkAccessManager = networkAccessManager
        self._request = QtNetwork.QNetworkRequest(self.url)
        self._request.setTransferTimeout(timeout)
        self._reply: QtNetwork.QNetworkReply | None = None
        self._error: Exceptions.AbortRequested | Exceptions.NetworkError | Playlist.Exceptions.InvalidPlaylist | None = None
        self._retryTimer = QtCore.QTimer(parent=self)
        self._retryTimer.setSingleShot(True)
        self._retryTimer.timeout.connect(self._retryTimerTimeout)
        self._maxRetryCount = maxRetryCount
        self._retryInterval = retryInterval
        self._running = False
        self._currentNetworkError: QtNetwork.QNetworkReply.NetworkError | None = None
        self._retryCount = 0
        self._nextSequence = 0

    def update(self) -> None:
        if self._reply == None:
            self._currentNetworkError = None
            self._retryCount = 0
            self._updatePlaylist()

    def _updatePlaylist(self) -> None:
        if self._reply == None:
            self._error = None
            self._running = True
            self._reply = self._networkAccessManager.get(self._request)
            self._reply.finished.connect(self._requestDone)

    def abort(self) -> None:
        self._raiseException(Exceptions.AbortRequested())

    def isRunning(self) -> bool:
        return self._running

    def _requestDone(self) -> None:
        reply = self._reply
        self._reply = None
        if self._error != None:
            return
        if reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            self._currentNetworkError = None
            try:
                self.playlist.loads(reply.readAll().data().decode(), baseUrl=self.url)
            except Exception as e:
                self._raiseException(e)
            else:
                self._running = False
                self.playlistUpdated.emit()
        elif self._currentNetworkError == QtNetwork.QNetworkReply.NetworkError.ContentAccessDenied and self._retryCount != 0:
            self._raiseException(Exceptions.NetworkError(reply))
        elif self._retryCount < self._maxRetryCount:
            self._currentNetworkError = reply.error()
            self._retryCount += 1
            self._retryTimer.start(self._retryInterval)
        else:
            self._raiseException(Exceptions.NetworkError(reply))

    def _raiseException(self, exception: Exceptions.AbortRequested | Exceptions.NetworkError | Playlist.Exceptions.InvalidPlaylist) -> None:
        if self._error != None:
            return
        self._error = exception
        if self._reply != None:
            self._reply.abort()
        if self._retryTimer.isActive():
            self._retryTimer.stop()
        self._running = False
        self.errorOccurred.emit(exception)

    def _retryTimerTimeout(self) -> None:
        self._updatePlaylist()

    def hasNewSegments(self) -> bool:
        segments = list(self.playlist.getRangedSegments(*self._range))
        if len(segments) == 0:
            return False
        else:
            return segments[-1].sequence >= self._nextSequence

    def getNewSegments(self) -> typing.Generator[Segment, None, None]:
        for segment in self.playlist.getRangedSegments(*self._range):
            if segment.sequence >= self._nextSequence:
                self._nextSequence = segment.sequence + 1
                yield segment

    def setRange(self, trimFrom: int | None, trimTo: int | None) -> None:
        self._range = (trimFrom, trimTo)

    def getRange(self) -> tuple[int | None, int | None]:
        return self._range

    def getSegmentRange(self) -> tuple[int | None, int | None]:
        return self.playlist.getSegmentRange(*self._range)