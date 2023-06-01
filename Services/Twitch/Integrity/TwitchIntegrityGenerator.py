from .TwitchIntegrity import Integrity
from .TwitchIntegrityConfig import Config

from Core.App import App
from Services.NetworkRequests import Network
from Services.Threading.MutexLocker import MutexLocker
from Services.Logging.ObjectLogger import ObjectLogger
from Database.Database import DB
from Ui.WebViewWidget import WebViewWidget

from PyQt6 import QtCore, QtWidgets, QtWebEngineCore


class Exceptions:
    class ThreadError(Exception):
        def __str__(self):
            return "Must be called from the main thread."


class IntegrityRequestInterceptor(QtWebEngineCore.QWebEngineUrlRequestInterceptor):
    intercepted = QtCore.pyqtSignal(object)

    def interceptRequest(self, info):
        if info.requestUrl().toString() == Config.INTEGRITY_URL and info.requestMethod().data().decode() == "POST":
            info.block(True)
            self.intercepted.emit({key.data().decode(): value.data().decode() for key, value in info.httpHeaders().items()})


class _TwitchIntegrityGenerator(QtCore.QObject):
    def __init__(self, parent=None):
        super(_TwitchIntegrityGenerator, self).__init__(parent=parent)
        interceptor = IntegrityRequestInterceptor(parent=self)
        interceptor.intercepted.connect(self.interceptedHandler)
        self.profile = QtWebEngineCore.QWebEngineProfile(parent=self)
        self.profile.setUrlRequestInterceptor(interceptor)
        self.integrity = None
        self.timeoutTimer = QtCore.QTimer(parent=self)
        self.timeoutTimer.setSingleShot(True)
        self.timeoutTimer.timeout.connect(self.timeoutHandler)
        self.timeoutTimer.setInterval(Config.TIMEOUT)
        self._mutexLocker = MutexLocker()

    def updateIntegrity(self, forceUpdate=False):
        if self.thread() != QtWidgets.QApplication.instance().thread():
            raise Exceptions.ThreadError
        if self.timeoutTimer.isActive():
            return
        elif self.hasValidIntegrity() and not forceUpdate:
            return
        else:
            App.logger.info("Updating Integrity(Forced)" if forceUpdate else "Updating Integrity")
            self._mutexLocker.lock()
            self.timeoutTimer.start()
            self.integrity = None
            self.webViewWidget = WebViewWidget()
            self.webViewWidget.setVisible(False)
            self.webViewWidget.setProfile(self.profile)
            self.webViewWidget.webView.load(QtCore.QUrl(Config.PAGE_URL))

    def interceptedHandler(self, data):
        self.timeoutTimer.stop()
        self.webViewWidget.close()
        del self.webViewWidget
        try:
            authToken = DB.account.getAuthToken()
            if authToken != "":
                data.update({"Authorization": f"OAuth {authToken}"})
            response = Network.session.post(Config.INTEGRITY_URL, headers=data)
            if response.status_code != 200:
                raise
            data = response.json()
            self.integrity = Integrity(
                headers=response.request.headers,
                token=data["token"],
                expiration=data["expiration"]
            )
            App.logger.info("Integrity Created")
            App.logger.debug(ObjectLogger.generateObjectLog(self.integrity))
        except Exception as e:
            App.logger.error("Unable to create integrity token.")
            App.logger.exception(e)
        self._mutexLocker.unlock()

    def timeoutHandler(self):
        self.webViewWidget.close()
        del self.webViewWidget
        self._mutexLocker.unlock()

    def hasValidIntegrity(self):
        if self.integrity != None:
            if self.integrity.isValid():
                return True
        return False

    def getIntegrity(self):
        self._mutexLocker.lock()
        self._mutexLocker.unlock()
        return self.integrity

TwitchIntegrityGenerator = _TwitchIntegrityGenerator()