from Core.Ui import *
from Services.Messages import Messages
from Services.Account.AccountData import AccountData
from Services.Account.BrowserAccountDetector import Exceptions, BrowserInfo, AvailableBrowsers
from Services.Twitch.GQL import TwitchGQLAPI


class Account(QtWidgets.QWidget):
    startLoginRequested = QtCore.pyqtSignal()
    cancelLoginRequested = QtCore.pyqtSignal()
    profileImageChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("account", self)
        self._ui.profileImage.setImageSizePolicy(QtCore.QSize(50, 50), QtCore.QSize(300, 300))
        self._ui.accountInfo.setText(T("#Log in and link the benefits of your Twitch account with {appName}.\n(Stream Ad-Free benefits, Subscriber-Only Stream access, Subscriber-Only Video access, Twitch Prime or Twitch Turbo benefits, etc.)", appName=CoreConfig.APP_NAME))
        self._ui.alertIcon = Utils.setSvgIcon(self._ui.alertIcon, Icons.ALERT_RED)
        self._ui.loginButton.clicked.connect(self.login)
        if Utils.isWindows():
            self._ui.importFromChromeButton.clicked.connect(self.importAccountFromChrome)
            self._ui.importFromEdgeButton.clicked.connect(self.importAccountFromEdge)
        else:
            self._ui.importAccountArea.hide()
        self._ui.continueButton.clicked.connect(self.startLoginRequested)
        self._ui.cancelButton.clicked.connect(self.cancelLoginRequested)
        self._ui.logoutButton.clicked.connect(self.logout)
        self._ui.refreshAccountButton.clicked.connect(self.refreshAccount)
        Utils.setIconViewer(self._ui.refreshAccountButton, Icons.RELOAD)
        self._ui.profileImage.imageChanged.connect(self.updateAccountImage)
        self._tempAccountData: AccountData | None = None
        App.Account.accountUpdated.connect(self.showAccount)
        App.Account.authorizationExpired.connect(self.authorizationExpired, QtCore.Qt.ConnectionType.QueuedConnection)

    def showLoading(self) -> None:
        self._ui.accountMenu.setCurrentIndex(0)
        self.updateAccountImage()

    def refreshAccount(self) -> None:
        App.Account.validateOAuthToken()
        if App.Account.isLoggedIn():
            self.showLoading()
            App.TwitchGQL.getChannel(id=App.Account.user.id).finished.connect(self._updateAccountDataResultHandler)
        elif self._tempAccountData != None:
            self.showLoading()
            App.TwitchGQL.getChannel(login=self._tempAccountData.username).finished.connect(self._updateAccountDataResultHandler)
        else:
            self.showAccount()

    def _updateAccountDataResultHandler(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            if self._tempAccountData == None:
                App.Account.user = response.getData().getUser()
            else:
                App.Account.login(
                    user=response.getData().getUser(),
                    token=self._tempAccountData.token,
                    expiration=self._tempAccountData.expiration
                )
        elif isinstance(response.getError(), TwitchGQLAPI.Exceptions.DataNotFound):
            App.Account.invalidate()
        self._tempAccountData = None
        self.showAccount()
        if response.getError() != None:
            if not isinstance(response.getError(), TwitchGQLAPI.Exceptions.DataNotFound):
                Utils.info("network-error", "#A network error occurred while loading your account data.", parent=self)

    def showAccount(self) -> None:
        if App.Account.isLoggedIn():
            self._ui.accountMenu.setCurrentIndex(2)
            self._ui.profileImage.loadImage(filePath=Images.PROFILE_IMAGE, url=App.Account.user.profileImageURL, urlFormatSize=ImageSize.USER_PROFILE, refresh=True)
            self._ui.account.setText(App.Account.user.displayName)
        else:
            self._ui.accountMenu.setCurrentIndex(1)
            self._ui.infoArea.hide()
            self._ui.buttonArea.setCurrentIndex(0)
            self._ui.importFromChromeButton.setEnabled(True)
            self._ui.importFromEdgeButton.setEnabled(True)
            self._ui.profileImage.cancelImageRequest()
            self.updateAccountImage()

    def authorizationExpired(self) -> None:
        Utils.info(*Messages.INFO.LOGIN_EXPIRED, parent=self)

    def updateAccountImage(self, image: QtGui.QPixmap | None = None) -> None:
        self.profileImageChanged.emit(image)

    def login(self) -> None:
        self._ui.infoArea.show()
        self._ui.buttonArea.setCurrentIndex(1)
        self._ui.importFromChromeButton.setEnabled(False)
        self._ui.importFromEdgeButton.setEnabled(False)
        self.startLoginRequested.emit()

    def processAccountData(self, accountData: AccountData) -> None:
        self._tempAccountData = accountData
        self.refreshAccount()

    def loginTabClosed(self) -> None:
        self._loginProcessComplete()

    def _loginProcessComplete(self) -> None:
        self._ui.infoArea.hide()
        self._ui.buttonArea.setCurrentIndex(0)
        self._ui.loginButton.setEnabled(True)
        self._ui.importFromChromeButton.setEnabled(True)
        self._ui.importFromEdgeButton.setEnabled(True)

    def logout(self) -> None:
        if Utils.ask("log-out", "#Are you sure you want to log out?", parent=self):
            App.Account.logout()

    def _confirmBrowserLogin(self, browserName: str) -> bool:
        return Utils.ask("information", T("#The Twitch account saved in your {browserName} browser will be detected and linked.\nSince {appName} shares the same account information as your browser, logging out of your Twitch account in the browser will also log you out of {appName}.\n\n\nBefore proceeding, please make sure that {browserName} is installed and that you are logged in to Twitch.\n\nAlso, please close all {browserName} windows and terminate any running {browserName} processes.", browserName=browserName, appName=Config.APP_NAME), contentTranslate=False, defaultOk=True, parent=self)

    def importAccountFromBrowser(self, browserInfo: BrowserInfo) -> None:
        if self._confirmBrowserLogin(browserName=browserInfo.getDisplayName()):
            self._ui.infoArea.show()
            self._ui.loginButton.setEnabled(False)
            self._ui.importFromChromeButton.setEnabled(False)
            self._ui.importFromEdgeButton.setEnabled(False)
            accountImportProgressView = Ui.AccountImportProgressView(browserInfo=browserInfo, parent=self)
            accountImportProgressView.accountDetected.connect(self.processAccountData, QtCore.Qt.ConnectionType.QueuedConnection)
            accountImportProgressView.errorOccurred.connect(self._accountImportError, QtCore.Qt.ConnectionType.QueuedConnection)
            accountImportProgressView.exec()
            self._loginProcessComplete()

    def importAccountFromChrome(self) -> None:
        self.importAccountFromBrowser(browserInfo=AvailableBrowsers.Chrome)

    def importAccountFromEdge(self) -> None:
        self.importAccountFromBrowser(browserInfo=AvailableBrowsers.Edge)

    def _accountImportError(self, browserInfo: BrowserInfo, exception: Exceptions.BrowserNotFound | Exceptions.DriverConnectionFailure | Exceptions.UnexpectedDriverError | Exceptions.AccountNotFound) -> None:
        if isinstance(exception, Exceptions.BrowserNotFound):
            Utils.info("error", T("#Unable to detect {browserName}.\nPlease make sure {browserName} is properly installed.", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)
        elif isinstance(exception, Exceptions.DriverConnectionFailure):
            Utils.info("error", T("#{browserName} is currently running.\nPlease close all {browserName} windows and try again.", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)
        elif isinstance(exception, Exceptions.UnexpectedDriverError):
            Utils.info("error", T("#An unexpected error occurred. Please ensure that the latest version of {browserName} is properly installed and all {browserName} windows are closed.", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)
        else:
            Utils.info("error", T("#Unable to find a Twitch account. Please make sure that {browserName} is logged in to Twitch.", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)