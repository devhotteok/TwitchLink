from ..Config import Config
from ..File import FileDownloadManager

from Core.GlobalExceptions import Exceptions
from Services.Playlist.Segment import Segment

from PyQt6 import QtCore, QtNetwork


class MutableSegmentDownloader(FileDownloadManager.FileDownloader):
    def __init__(self, networkAccessManager: QtNetwork.QNetworkAccessManager, segment: Segment, filePath: str, priority: int = 0, parent: QtCore.QObject | None = None):
        self.segment = segment
        fileName = self.segment.url.fileName()
        if "." in fileName:
            name, extension = fileName.rsplit(".", 1)
        else:
            name = fileName
            extension = None
        for key in ["-muted", "-unmuted"]:
            if name.endswith(key):
                name = name.rsplit(key, 1)[0]
                break
        if extension == None:
            self._originalUrl = self.segment.url.resolved(QtCore.QUrl(name))
            self._mutedUrl = self.segment.url.resolved(QtCore.QUrl(f"{name}-muted"))
            self._unmutedUrl = self.segment.url.resolved(QtCore.QUrl(f"{name}-unmuted"))
        else:
            self._originalUrl = self.segment.url.resolved(QtCore.QUrl(f"{name}.{extension}"))
            self._mutedUrl = self.segment.url.resolved(QtCore.QUrl(f"{name}-muted.{extension}"))
            self._unmutedUrl = self.segment.url.resolved(QtCore.QUrl(f"{name}-unmuted.{extension}"))
        super().__init__(networkAccessManager, self._originalUrl, filePath, priority=priority, parent=parent)
        self._unmuted = False
        self._muted = False

    def getPriority(self) -> int:
        return super().getPriority() + 1 if self._unmuted or self._muted else 0

    def _raiseException(self, exception: Exceptions.AbortRequested | Exceptions.FileSystemError | Exceptions.NetworkError) -> None:
        if self._error != None:
            return
        self._error = exception
        if self._reply != None:
            self._reply.abort()
        if self._retryTimer.isActive():
            self._retryTimer.stop()
        if isinstance(exception, Exceptions.NetworkError) and (self._unmuted == False or self._muted == False):
            self._retryScheduled = True
            self._error = None
            if self._unmuted == False:
                self._unmuted = True
                self.url = self._unmutedUrl
            else:
                self._muted = True
                self.url = self._mutedUrl
            self._request.setUrl(self.url)
            self._retryRequired.emit(self)
            self._retryTimerTimeout()
        elif isinstance(exception, Exceptions.NetworkError) and self._retryCount < Config.FILE_REQUEST_MAX_RETRY_COUNT:
            self._unmuted = False
            self._muted = False
            self._retryCount += 1
            self._retryScheduled = True
            self._error = None
            self._request.setUrl(self._originalUrl)
            self._retryRequired.emit(self)
            self._retryTimer.start(self._retryCount * Config.FILE_REQUEST_RETRY_INTERVAL)
        else:
            self.errorOccurred.emit(self)
            self._setFinished()

    def isMuted(self) -> bool:
        return self._muted