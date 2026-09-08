from Core.Ui import *
from Services.Messages import Messages
from Services.Account.AccountData import AccountData
from Services.Account.ExternalBrowserDriver import BrowserInfo as BrowserDriverBrowserInfo, AvailableBrowsers as BrowserDriverAvailableBrowsers
from Services.Account.BrowserAccountDetector import Exceptions, BrowserInfo as BrowserAccountDetectorBrowserInfo, AvailableBrowsers as BrowserAccountDetectorAvailableBrowsers
from Services.Twitch.GQL import TwitchGQLAPI


class Account(QtWidgets.QWidget):
    startSignInRequested = QtCore.pyqtSignal()
    cancelSignInRequested = QtCore.pyqtSignal()
    profileImageChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("account", self)
        self._ui.profileImage.setImageSizePolicy(QtCore.QSize(50, 50), QtCore.QSize(300, 300))

        self._ui.alertIcon = Utils.setSvgIcon(self._ui.alertIcon, Icons.ALERT_RED)
        self._ui.signInWithChromeButton.clicked.connect(self.signInWithChrome)
        self._ui.signInWithEdgeButton.clicked.connect(self.signInWithEdge)
        if Utils.isWindows():
            self._ui.importFromFirefoxButton.clicked.connect(self.importAccountFromFirefox)
        else:
            self._ui.importFromFirefoxButton.hide()
        self._ui.signInButton.clicked.connect(self.signIn)
        self._ui.continueButton.clicked.connect(self.startSignInRequested)
        self._ui.cancelButton.clicked.connect(self.cancelSignInRequested)
        self._ui.signOutButton.clicked.connect(self.signOut)
        self._ui.refreshAccountButton.clicked.connect(self.refreshAccount)
        Utils.setIconViewer(self._ui.refreshAccountButton, Icons.RELOAD)
        self._ui.profileImage.imageChanged.connect(self.updateAccountImage)
        self._tempAccountData: AccountData | None = None
        App.Account.accountUpdated.connect(self.showAccount)
        App.Account.authorizationExpired.connect(self.authorizationExpired, QtCore.Qt.ConnectionType.QueuedConnection)
        self.retranslateDynamicUi()

    def showLoading(self) -> None:
        self._ui.accountMenu.setCurrentIndex(0)
        self.updateAccountImage()

    def refreshAccount(self) -> None:
        App.Account.validateOAuthToken()
        if App.Account.isSignedIn():
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
                App.Account.signIn(
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
                Utils.info("network-error", "errors.#a_network_error_occurred_while_loading", parent=self)

    def showAccount(self) -> None:
        if App.Account.isSignedIn():
            self._ui.accountMenu.setCurrentIndex(2)
            self._ui.profileImage.loadImage(filePath=Images.PROFILE_IMAGE, url=App.Account.user.profileImageURL, urlFormatSize=ImageSize.USER_PROFILE, refresh=True)
            self._ui.account.setText(App.Account.user.displayName)
        else:
            self._ui.accountMenu.setCurrentIndex(1)
            self._ui.infoArea.hide()
            self._ui.buttonArea.setCurrentIndex(0)
            self._ui.signInWithChromeButton.setEnabled(True)
            self._ui.signInWithEdgeButton.setEnabled(True)
            self._ui.importFromFirefoxButton.setEnabled(True)
            self._ui.profileImage.cancelImageRequest()
            self.updateAccountImage()

    def authorizationExpired(self) -> None:
        Utils.info(*Messages.INFO.SESSION_EXPIRED, parent=self)

    def updateAccountImage(self, image: QtGui.QPixmap | None = None) -> None:
        self.profileImageChanged.emit(image)

    def signIn(self) -> None:
        self._ui.infoArea.show()
        self._ui.buttonArea.setCurrentIndex(1)
        self._ui.signInWithChromeButton.setEnabled(False)
        self._ui.signInWithEdgeButton.setEnabled(False)
        self._ui.importFromFirefoxButton.setEnabled(False)
        self.startSignInRequested.emit()

    def processAccountData(self, accountData: AccountData) -> None:
        self._tempAccountData = accountData
        self.refreshAccount()

    def signInTabClosed(self) -> None:
        self._signInProcessComplete()

    def _signInProcessComplete(self) -> None:
        self._ui.infoArea.hide()
        self._ui.buttonArea.setCurrentIndex(0)
        self._ui.signInButton.setEnabled(True)
        self._ui.signInWithChromeButton.setEnabled(True)
        self._ui.signInWithEdgeButton.setEnabled(True)
        self._ui.importFromFirefoxButton.setEnabled(True)

    def signOut(self) -> None:
        if Utils.ask("sign-out", "prompts.#are_you_sure_you_want_sign_out", parent=self):
            App.Account.signOut()

    def _openExternalBrowser(self, browserInfo: BrowserDriverBrowserInfo) -> None:
        self._ui.infoArea.show()
        self._ui.signInButton.setEnabled(False)
        self._ui.signInWithChromeButton.setEnabled(False)
        self._ui.signInWithEdgeButton.setEnabled(False)
        self._ui.importFromFirefoxButton.setEnabled(False)
        externalBrowserLauncher = Ui.ExternalBrowserLauncher(browserInfo=browserInfo, parent=self)
        externalBrowserLauncher.accountDetected.connect(self.processAccountData, QtCore.Qt.ConnectionType.QueuedConnection)
        externalBrowserLauncher.errorOccurred.connect(self._externalBrowserError, QtCore.Qt.ConnectionType.QueuedConnection)
        externalBrowserLauncher.exec()
        self._signInProcessComplete()

    def _externalBrowserError(self, browserInfo: BrowserDriverBrowserInfo) -> None:
        Utils.info("error", T("errors.#an_unexpected_error_occurred_while_laun", browserName=browserInfo.getDisplayName()), parent=self)

    def _confirmBrowserSignIn(self, browserName: str) -> bool:
        return Utils.ask("information", T("prompts.#the_twitch_account_saved_your_browser_w", browserName=browserName, appName=Config.APP_NAME), contentTranslate=False, defaultOk=True, parent=self)

    def importAccountFromBrowser(self, browserInfo: BrowserAccountDetectorBrowserInfo) -> None:
        if self._confirmBrowserSignIn(browserName=browserInfo.getDisplayName()):
            self._ui.infoArea.show()
            self._ui.signInButton.setEnabled(False)
            self._ui.signInWithChromeButton.setEnabled(False)
            self._ui.signInWithEdgeButton.setEnabled(False)
            self._ui.importFromFirefoxButton.setEnabled(False)
            accountImportProgressView = Ui.AccountImportProgressView(browserInfo=browserInfo, parent=self)
            accountImportProgressView.accountDetected.connect(self.processAccountData, QtCore.Qt.ConnectionType.QueuedConnection)
            accountImportProgressView.errorOccurred.connect(self._accountImportError, QtCore.Qt.ConnectionType.QueuedConnection)
            accountImportProgressView.exec()
            self._signInProcessComplete()

    def signInWithChrome(self) -> None:
        self._openExternalBrowser(browserInfo=BrowserDriverAvailableBrowsers.Chrome)

    def signInWithEdge(self) -> None:
        self._openExternalBrowser(browserInfo=BrowserDriverAvailableBrowsers.Edge)

    def importAccountFromFirefox(self) -> None:
        self.importAccountFromBrowser(browserInfo=BrowserAccountDetectorAvailableBrowsers.Firefox)

    def _accountImportError(self, browserInfo: BrowserAccountDetectorBrowserInfo, exception: Exceptions.BrowserNotFound | Exceptions.DriverConnectionFailure | Exceptions.UnexpectedDriverError | Exceptions.AccountNotFound) -> None:
        if isinstance(exception, Exceptions.BrowserNotFound):
            Utils.info("error", T("errors.#unable_detect_please_make_sure_is_prope", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)
        elif isinstance(exception, Exceptions.DriverConnectionFailure):
            Utils.info("error", T("errors.#failed_connect_if_is_currently_running", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)
        elif isinstance(exception, Exceptions.UnexpectedDriverError):
            Utils.info("error", T("errors.#an_unexpected_error_occurred_please_ens", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)
        else:
            Utils.info("error", T("errors.#unable_find_twitch_account_please_make", browserName=browserInfo.getDisplayName()), contentTranslate=False, parent=self)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)
            self.retranslateDynamicUi()

    def retranslateDynamicUi(self) -> None:
        self._ui.accountInfo.setText(T("messages.#sign_and_link_benefits_your_twitch_acco", appName=CoreConfig.APP_NAME))
