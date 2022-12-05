from Core.Ui import *
from Ui.Components.Operators.WebViewTabManager import WebViewTabManager
from Ui.Components.Widgets.LoginWidget import LoginWidget


class AccountPage(WebViewTabManager):
    loginTabClosed = QtCore.pyqtSignal()

    def __init__(self, pageObject, parent=None):
        super(AccountPage, self).__init__(parent=parent)
        self.pageObject = pageObject
        self.account = Ui.Account(parent=self)
        self.account.startLoginRequested.connect(self.openLogin)
        self.account.cancelLoginRequested.connect(self.closeLogin)
        self.account.profileImageChanged.connect(self.profileImageChanged)
        self.loginTabClosed.connect(self.account.loginTabClosed)
        self.addTab(self.account, icon=Icons.ACCOUNT_ICON, closable=False)

    def profileImageChanged(self, icon):
        if icon == None:
            self.pageObject.setPageIcon(Icons.ACCOUNT_ICON)
        else:
            self.pageObject.setPageIcon(icon, size=QtCore.QSize(32, 32))

    def refreshAccount(self):
        self.account.refreshAccount()

    def openLogin(self):
        tabIndex = self.getUniqueTabIndex(LoginWidget)
        if tabIndex == None:
            try:
                loginWidget = LoginWidget(parent=self)
            except:
                self.loginTabClosed.emit()
                Utils.info("error", "#This module cannot be loaded.", parent=self)
                return
            loginWidget.loginComplete.connect(self.loginCompleteHandler)
            tabIndex = self.addWebTab(loginWidget, uniqueValue=LoginWidget)
        self.setCurrentIndex(tabIndex)

    def loginCompleteHandler(self, accountData):
        self.account.loginResultHandler(accountData)
        self.closeLogin()

    def closeLogin(self):
        self.closeAllWebTabs()
        self.loginTabClosed.emit()

    def closeTab(self, index):
        if index == self.getUniqueTabIndex(LoginWidget):
            self.account.cancelLogin()
        else:
            super().closeTab(index)