from Core.Ui import *
from Ui.Components.Operators.NavigationBar import PageObject
from Ui.Components.Operators.WebViewTabManager import WebViewTabManager
from Ui.Components.Widgets.LoginWidget import LoginWidget, AccountData

from PyQt6 import QtWebEngineCore


class AccountPage(WebViewTabManager):
    def __init__(self, pageObject: PageObject, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.pageObject = pageObject
        self.account = Ui.Account(parent=self)
        self.account.startLoginRequested.connect(self._startLoginRequested)
        self.account.cancelLoginRequested.connect(self._cancelLoginRequested)
        self.account.profileImageChanged.connect(self._profileImageChanged)
        self.addTab(self.account, icon=Icons.ACCOUNT, closable=False)
        self._profile: QtWebEngineCore.QWebEngineProfile | None = None
        self._closing = False

    def _profileImageChanged(self, image: QtGui.QPixmap | None) -> None:
        if image == None:
            self.pageObject.setPageIcon(Icons.ACCOUNT)
        else:
            self.pageObject.setPageIcon(QtGui.QIcon(image), size=QtCore.QSize(32, 32))

    def refreshAccount(self) -> None:
        self.account.refreshAccount()

    def _startLoginRequested(self) -> None:
        tabIndex = self.getUniqueTabIndex(LoginWidget)
        if tabIndex == None:
            self._profile = QtWebEngineCore.QWebEngineProfile(parent=self)
            loginWidget = LoginWidget(self._profile, parent=self)
            loginWidget.loginComplete.connect(self._loginCompleteHandler)
            tabIndex = self.addWebTab(loginWidget, uniqueValue=LoginWidget)
        self.setCurrentIndex(tabIndex)

    def _cancelLoginRequested(self) -> None:
        if Utils.ask("cancel-login", "#Are you sure you want to cancel the login operation in progress?", parent=self):
            self.closeLogin()

    def _loginCompleteHandler(self, accountData: AccountData) -> None:
        self.account.processAccountData(accountData)
        self.closeLogin()

    def closeLogin(self) -> None:
        self._closing = True
        self.closeAllWebTabs()
        self._profile.deleteLater()
        self._profile = None
        self._closing = False
        self.account.loginTabClosed()

    def closeTab(self, index: int) -> None:
        if index == self.getUniqueTabIndex(LoginWidget):
            if self._closing:
                super().closeTab(index)
            else:
                self._cancelLoginRequested()
        else:
            super().closeTab(index)