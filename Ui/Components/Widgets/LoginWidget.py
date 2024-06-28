from Core.Ui import *
from Services.Account.Config import Config
from Ui.WebViewWidget import WebViewWidget

from PyQt6 import QtWebEngineCore, QtNetwork


class AccountData:
    def __init__(self):
        self.username: str | None = None
        self.token: str | None = None
        self.expiration: int | None = None


class LoginWidget(WebViewWidget):
    loginComplete = QtCore.pyqtSignal(AccountData)

    def __init__(self, profile: QtWebEngineCore.QWebEngineProfile, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.accountData = AccountData()
        self.profile = profile
        self.profile.cookieStore().cookieAdded.connect(self._getOAuthToken)
        self.setProfile(self.profile)
        self.showLoginPage()

    def showLoginPage(self) -> None:
        self._ui.webView.load(QtCore.QUrl(Config.LOGIN_PAGE))

    def urlChangeHandler(self, url: QtCore.QUrl) -> None:
        super().urlChangeHandler(url)
        if url.toString() != Config.LOGIN_PAGE:
            self.showInfo(T("#You left the login page."), icon=Icons.ALERT_RED, buttonIcon=Icons.LOGIN, buttonText=T("#Return to login page"), buttonHandler=self.showLoginPage)
        else:
            self.showInfo(T("#Please follow the login procedure."), icon=Icons.INFO)

    def hasAccountData(self) -> bool:
        return self.accountData.username != None and self.accountData.token != None

    def setUsernameData(self, username: str) -> None:
        self.accountData.username = username

    def setTokenData(self, token: str, expiration: QtCore.QDateTime) -> None:
        self.accountData.token = token
        self.accountData.expiration = None if expiration.isNull() else expiration.toSecsSinceEpoch()

    def _getOAuthToken(self, cookie: QtNetwork.QNetworkCookie) -> None:
        if cookie.domain() == Config.COOKIE_DOMAIN:
            if cookie.name() == Config.COOKIE_USERNAME:
                self.setUsernameData(cookie.value().data().decode(errors="ignore"))
                self._checkToken()
            elif cookie.name() == Config.COOKIE_AUTH_TOKEN:
                self.setTokenData(cookie.value().data().decode(errors="ignore"), cookie.expirationDate())
                self._checkToken()

    def _checkToken(self) -> None:
        if self.hasAccountData():
            self.profile.cookieStore().cookieAdded.disconnect(self._getOAuthToken)
            self.loginComplete.emit(self.accountData)