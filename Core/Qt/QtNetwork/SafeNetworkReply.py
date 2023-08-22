from PyQt6 import QtCore, QtNetwork

import typing


class SafeNetworkReply(QtCore.QObject):
    _internalRuntimeError = QtCore.pyqtSignal()
    readyRead = QtCore.pyqtSignal()
    downloadProgress = QtCore.pyqtSignal(object, object)
    errorOccurred = QtCore.pyqtSignal(QtNetwork.QNetworkReply.NetworkError)
    finished = QtCore.pyqtSignal()

    def __init__(self, request: QtNetwork.QNetworkRequest, reply: QtNetwork.QNetworkReply, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._request: QtNetwork.QNetworkRequest | None = request
        self._reply: QtNetwork.QNetworkReply | None = reply
        self._runtimeError: RuntimeError | None = None
        self._errorSignalEmitted: bool = False
        self._finished: bool = False
        self._internalRuntimeError.connect(self._processRuntimeErrorSignals, QtCore.Qt.ConnectionType.QueuedConnection)
        try:
            if self._reply.isFinished():
                self._replyFinished()
            else:
                self._reply.readyRead.connect(self._replyReadyRead)
                self._reply.downloadProgress.connect(self._replyDownloadProgress)
                self._reply.errorOccurred.connect(self._replyErrorOccurred)
                self._reply.finished.connect(self._replyFinished)
        except RuntimeError as e:
            self._handleRuntimeError(e)

    def _replyReadyRead(self) -> None:
        if not self._finished:
            self.readyRead.emit()

    def _replyDownloadProgress(self, bytesReceived: int, bytesTotal: int) -> None:
        if not self._finished:
            self.downloadProgress.emit(bytesReceived, bytesTotal)

    def _replyErrorOccurred(self, error: QtNetwork.QNetworkReply.NetworkError) -> None:
        if not self._errorSignalEmitted and not self._finished:
            self._errorSignalEmitted = True
            self.errorOccurred.emit(error)

    def _replyFinished(self) -> None:
        if not self._finished:
            self._finished = True
            self.finished.emit()
            self.deleteLater()

    def request(self) -> QtNetwork.QNetworkRequest:
        if not self._hasRuntimeError():
            try:
                return self._reply.request()
            except RuntimeError as e:
                self._handleRuntimeError(e)
        return self._request

    def url(self) -> QtCore.QUrl:
        if not self._hasRuntimeError():
            try:
                return self._reply.url()
            except RuntimeError as e:
                self._handleRuntimeError(e)
        return self._request.url()

    def attribute(self, code: QtNetwork.QNetworkRequest.Attribute) -> typing.Any:
        if not self._hasRuntimeError():
            try:
                return self._reply.attribute(code)
            except RuntimeError as e:
                self._handleRuntimeError(e)
        return None

    def readAll(self) -> QtCore.QByteArray:
        if not self._hasRuntimeError():
            try:
                return self._reply.readAll()
            except RuntimeError as e:
                self._handleRuntimeError(e)
        return QtCore.QByteArray()

    def abort(self) -> None:
        if not self._hasRuntimeError():
            try:
                self._reply.abort()
            except RuntimeError as e:
                self._handleRuntimeError(e)

    def error(self) -> QtNetwork.QNetworkReply.NetworkError:
        if not self._hasRuntimeError():
            try:
                return self._reply.error()
            except RuntimeError as e:
                self._handleRuntimeError(e)
        return QtNetwork.QNetworkReply.NetworkError.UnknownNetworkError

    def errorString(self) -> str:
        if not self._hasRuntimeError():
            try:
                return self._reply.errorString()
            except RuntimeError as e:
                self._handleRuntimeError(e)
        return f"Unexpected Runtime Error (QNetworkReply may have been deleted for unknown reasons.)\n{self._runtimeError}"

    def _hasRuntimeError(self) -> bool:
        return self._runtimeError != None

    def _handleRuntimeError(self, exception: RuntimeError) -> None:
        self._runtimeError = exception
        self._internalRuntimeError.emit()

    def _processRuntimeErrorSignals(self) -> None:
        self._replyErrorOccurred(self.error())
        self._replyFinished()