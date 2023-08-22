from ..Config import Config

from Core.GlobalExceptions import Exceptions

from PyQt6 import QtCore, QtNetwork


class FileDownloader(QtCore.QObject):
    progressChanged = QtCore.pyqtSignal(object, object)
    errorOccurred = QtCore.pyqtSignal(object)
    finished = QtCore.pyqtSignal(object)
    _startRequested = QtCore.pyqtSignal()
    _abortRequested = QtCore.pyqtSignal(object)
    _retryRequired = QtCore.pyqtSignal(object)
    _retryRequested = QtCore.pyqtSignal(object)

    def __init__(self, networkAccessManager: QtNetwork.QNetworkAccessManager, url: QtCore.QUrl, filePath: str, priority: int = 0, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.url = url
        self.filePath = filePath
        self._priority = priority
        self.file = QtCore.QFile(self.filePath, self)
        self.bytesReceived = 0
        self.bytesTotal = 0
        self._networkAccessManager = networkAccessManager
        self._request = QtNetwork.QNetworkRequest(self.url)
        self._request.setTransferTimeout(Config.FILE_REQUEST_TIMEOUT)
        self._reply: QtNetwork.QNetworkReply | None = None
        self._error: Exceptions.AbortRequested | Exceptions.FileSystemError | Exceptions.NetworkError | None = None
        self._retryScheduled: bool = False
        self._retryCount = 0
        self._finished = False
        self._retryTimer = QtCore.QTimer(parent=self)
        self._retryTimer.setSingleShot(True)
        self._retryTimer.timeout.connect(self._retryTimerTimeout)
        self._startRequested.connect(self._startHandler)
        self._abortRequested.connect(self._abortHandler)

    def getPriority(self) -> int:
        return self._priority * (Config.FILE_REQUEST_MAX_RETRY_COUNT + 1) + self._retryCount

    def start(self) -> None:
        self._startRequested.emit()

    def _startHandler(self) -> None:
        if self._reply == None:
            self._setDownloadProgress(0, 0)
            if not self.file.open(QtCore.QIODevice.OpenModeFlag.WriteOnly):
                self._raiseException(Exceptions.FileSystemError(self.file))
                return
            self._reply = self._networkAccessManager.get(self._request)
            self._reply.readyRead.connect(self._onReadyRead)
            self._reply.downloadProgress.connect(self._setDownloadProgress)
            self._reply.errorOccurred.connect(self._onNetworkError)
            self._reply.finished.connect(self._onFinished)

    def abort(self, reason: str | None = None) -> None:
        self._abortRequested.emit(reason)

    def _abortHandler(self, reason: str | None = None) -> None:
        self._raiseException(Exceptions.AbortRequested(reason))

    def getError(self) -> Exceptions.AbortRequested | Exceptions.FileSystemError | Exceptions.NetworkError | None:
        return self._error

    def _setDownloadProgress(self, bytesReceived: int, bytesTotal: int) -> None:
        self.bytesReceived = bytesReceived
        self.bytesTotal = bytesTotal
        self.progressChanged.emit(self.bytesReceived, self.bytesTotal)

    def _onReadyRead(self) -> None:
        if self._reply.attribute(QtNetwork.QNetworkRequest.Attribute.HttpStatusCodeAttribute) == 200:
            bytesWritten = self.file.write(self._reply.readAll())
            if bytesWritten == -1:
                self._raiseException(Exceptions.FileSystemError(self.file))

    def _onFinished(self) -> None:
        self.file.close()
        self._reply = None
        if self._retryScheduled:
            self.file.remove()
        elif self._error == None:
            self._setFinished()

    def _onNetworkError(self, error: QtNetwork.QNetworkReply.NetworkError) -> None:
        self._raiseException(Exceptions.NetworkError(self._reply))

    def _raiseException(self, exception: Exceptions.AbortRequested | Exceptions.FileSystemError | Exceptions.NetworkError) -> None:
        if self._error != None:
            return
        self._error = exception
        if self._reply != None:
            self._reply.abort()
        if self._retryTimer.isActive():
            self._retryTimer.stop()
        if isinstance(exception, Exceptions.NetworkError) and self._retryCount < Config.FILE_REQUEST_MAX_RETRY_COUNT:
            self._retryCount += 1
            self._retryScheduled = True
            self._error = None
            self._retryRequired.emit(self)
            self._retryTimer.start(self._retryCount * Config.FILE_REQUEST_RETRY_INTERVAL)
        else:
            self.errorOccurred.emit(self)
            self._setFinished()

    def _retryTimerTimeout(self) -> None:
        if self._error == None:
            self._retryScheduled = False
            self._retryRequested.emit(self)

    def _setFinished(self) -> None:
        if not self._finished:
            self._finished = True
            self.finished.emit(self)

    def isFinished(self) -> bool:
        return self._finished