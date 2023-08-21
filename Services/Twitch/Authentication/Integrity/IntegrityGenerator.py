from .IntegrityToken import IntegrityToken
from .IntegrityConfig import Config

from Core import App
from Core import GlobalExceptions
from Services.Logging.Logger import Logger

from PyQt6 import QtCore, QtNetwork, QtWebEngineCore, QtWebEngineWidgets

import typing
import json


class Exceptions(GlobalExceptions.Exceptions):
    class ThreadError(Exception):
        def __str__(self):
            return "This function must be called from the main thread."


class IntegrityRequestInterceptor(QtWebEngineCore.QWebEngineUrlRequestInterceptor):
    intercepted = QtCore.pyqtSignal(dict)

    def interceptRequest(self, info: QtWebEngineCore.QWebEngineUrlRequestInfo) -> None:
        if info.requestUrl().toString() == Config.INTEGRITY_URL and info.requestMethod().data().decode() == "POST":
            info.block(True)
            self.intercepted.emit({key.data().decode(): value.data().decode() for key, value in info.httpHeaders().items()})


class TwitchIntegrityGenerator(QtCore.QObject):
    _updateRequested = QtCore.pyqtSignal()
    _integrityUpdated = QtCore.pyqtSignal(object)

    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.logger = logger
        self.integrity = None
        self._isUpdating = False
        interceptor = IntegrityRequestInterceptor(parent=self)
        interceptor.intercepted.connect(self._interceptedHandler)
        self._profile = QtWebEngineCore.QWebEngineProfile(parent=self)
        self._profile.setUrlRequestInterceptor(interceptor)
        self._webEngineView: QtWebEngineWidgets.QWebEngineView | None = None
        self._headers: dict | None = None
        self._reply: QtNetwork.QNetworkReply | None = None
        self._timeoutTimer = QtCore.QTimer(parent=self)
        self._timeoutTimer.setSingleShot(True)
        self._timeoutTimer.setInterval(Config.TIMEOUT)
        self._timeoutTimer.timeout.connect(self._webEngineViewtimeoutHandler)
        self._updateRequested.connect(self.updateIntegrity)

    def updateIntegrity(self, forceUpdate: bool = False) -> None:
        if QtCore.QThread.currentThread() != App.Instance.thread():
            raise Exceptions.ThreadError
        if self._isUpdating:
            return
        elif self.hasValidIntegrity() and not forceUpdate:
            self._integrityUpdated.emit(self.integrity)
        else:
            self.logger.info("Updating Integrity(Forced)" if forceUpdate else "Updating Integrity")
            self._timeoutTimer.start()
            self._createWebEngineView()

    def _createWebEngineView(self) -> None:
        self._isUpdating = True
        self.integrity = None
        self._webEngineView = QtWebEngineWidgets.QWebEngineView()
        self._webEngineView.setVisible(False)
        self._webEngineView.setPage(QtWebEngineCore.QWebEnginePage(self._profile, self._webEngineView))
        self._webEngineView.load(QtCore.QUrl(Config.ACCOUNT_PAGE_URL))

    def _webEngineViewtimeoutHandler(self) -> None:
        if self._webEngineView == None:
            return
        self._webEngineView.close()
        self._webEngineView = None
        self._isUpdating = False
        self._integrityUpdated.emit(self.integrity)

    def _interceptedHandler(self, headers: dict) -> None:
        if self._webEngineView == None:
            return
        self._timeoutTimer.stop()
        self._webEngineView.close()
        self._webEngineView = None
        oAuthToken = App.Account.getOAuthToken()
        if oAuthToken != "":
            headers.update({"Authorization": f"OAuth {oAuthToken}"})
        self._headers = headers
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(Config.INTEGRITY_URL))
        for key, value in headers.items():
            request.setRawHeader(key.encode(), value.encode())
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self._reply = App.NetworkAccessManager.post(request, QtCore.QByteArray())
        self._reply.finished.connect(self._requestDone)

    def _requestDone(self) -> None:
        if self._reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            try:
                data = json.loads(self._reply.readAll().data().decode())
                self.integrity = IntegrityToken(
                    headers=self._headers,
                    value=data["token"],
                    expiration=data["expiration"]
                )
            except:
                self.logger.error("Unable to update integrity token.")
                self.logger.exception(Exceptions.UnexpectedError())
            else:
                self.logger.info("Integrity Updated")
                self.logger.debug(Logger.generateObjectLog(self.integrity))
        else:
            self.logger.error("Unable to update integrity token.")
            self.logger.exception(Exceptions.NetworkError(self._reply))
        self._headers = None
        self._reply = None
        self._isUpdating = False
        self._integrityUpdated.emit(self.integrity)

    def hasValidIntegrity(self) -> bool:
        if self.integrity != None:
            if self.integrity.isValid():
                return True
        return False

    def getIntegrity(self, callback: typing.Callable) -> None:
        self._integrityUpdated.connect(callback, QtCore.Qt.ConnectionType.SingleShotConnection)
        self._updateRequested.emit()