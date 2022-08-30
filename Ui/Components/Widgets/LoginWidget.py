from Core.Ui import *
from Services.Account.Config import Config
from Ui.WebViewWidget import WebViewWidget

from PyQt5 import QtCore


class AccountData:
    def __init__(self):
        self.username = None
        self.token = None
        self.expiry = None


class LoginWidget(WebViewWidget):
    loginComplete = QtCore.pyqtSignal(AccountData)

    def __init__(self, parent=None):
        super(LoginWidget, self).__init__(parent=parent)
        self.accountData = AccountData()
        self.profile = QtWebEngineWidgets.QWebEngineProfile(parent=self)
        self.profile.cookieStore().cookieAdded.connect(self.getAuthToken)
        self.setProfile(self.profile)
        self.showLoginPage()

    def showLoginPage(self):
        self.webView.load(QtCore.QUrl(Config.LOGIN_PAGE))

    def urlChangeHandler(self, url):
        super().urlChangeHandler(url)
        if url.toString() != Config.LOGIN_PAGE:
            self.showInfo(T("#You left the login page."), icon=Icons.ALERT_RED_ICON, buttonIcon=Icons.LOGIN_ICON, buttonText=T("#Return to login page"), buttonHandler=self.showLoginPage)
        else:
            self.showInfo(T("#Please follow the login procedure."), icon=Icons.INFO_ICON)

    def hasAccountData(self):
        return self.accountData.username != None and self.accountData.token != None

    def setUsernameData(self, username):
        self.accountData.username = username

    def setTokenData(self, token, expiry):
        self.accountData.token = token
        self.accountData.expiry = None if expiry.isNull() else expiry

    def getAuthToken(self, cookie):
        if cookie.domain() == Config.COOKIE_DOMAIN:
            if cookie.name() == Config.COOKIE_USERNAME:
                self.setUsernameData(cookie.value().data().decode())
                self.checkToken()
            elif cookie.name() == Config.COOKIE_AUTH_TOKEN:
                self.setTokenData(cookie.value().data().decode(), cookie.expirationDate())
                self.checkToken()

    def checkToken(self):
        if self.hasAccountData():
            self.profile.cookieStore().cookieAdded.disconnect(self.getAuthToken)
            self.loginComplete.emit(self.accountData)