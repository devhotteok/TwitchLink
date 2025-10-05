from Core.Ui import *
from Services.Account.AccountData import AccountData
from Ui.Components.Operators.NavigationBar import PageObject
from Ui.Components.Operators.WebViewTabManager import WebViewTabManager
from Ui.Components.Widgets.SignInWidget import SignInWidget

from PyQt6 import QtWebEngineCore


class AccountPage(WebViewTabManager):
    def __init__(self, pageObject: PageObject, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.pageObject = pageObject
        self.account = Ui.Account(parent=self)
        self.account.startSignInRequested.connect(self._startSignInRequested)
        self.account.cancelSignInRequested.connect(self._cancelSignInRequested)
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

    def _startSignInRequested(self) -> None:
        tabIndex = self.getUniqueTabIndex(SignInWidget)
        if tabIndex == None:
            self._profile = QtWebEngineCore.QWebEngineProfile(parent=self)
            signInWidget = SignInWidget(self._profile, parent=self)
            signInWidget.signInComplete.connect(self._signInCompleteHandler)
            tabIndex = self.addWebTab(signInWidget, uniqueValue=SignInWidget)
        self.setCurrentIndex(tabIndex)

    def _cancelSignInRequested(self) -> None:
        if Utils.ask("cancel-sign-in", "#Are you sure you want to cancel the sign-in operation in progress?", parent=self):
            self.closeSignIn()

    def _signInCompleteHandler(self, accountData: AccountData) -> None:
        self.account.processAccountData(accountData)
        self.closeSignIn()

    def closeSignIn(self) -> None:
        self._closing = True
        self.closeAllWebTabs()
        self._profile.deleteLater()
        self._profile = None
        self._closing = False
        self.account.signInTabClosed()

    def closeTab(self, index: int) -> None:
        if index == self.getUniqueTabIndex(SignInWidget):
            if self._closing:
                super().closeTab(index)
            else:
                self._cancelSignInRequested()
        else:
            super().closeTab(index)