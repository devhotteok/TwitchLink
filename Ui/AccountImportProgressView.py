from Core.Ui import *
from Services.Account.AccountData import AccountData
from Services.Account.BrowserAccountDetector import BrowserAccountDetector, BrowserProfile, BrowserInfo


class AccountImportProgressView(QtWidgets.QDialog):
    accountDetected = QtCore.pyqtSignal(AccountData)
    errorOccurred = QtCore.pyqtSignal(BrowserInfo, Exception)

    def __init__(self, browserInfo: BrowserInfo, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("accountImportProgressView", self)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowCloseButtonHint, False)
        self.accountDetector = BrowserAccountDetector(parent=self)
        self.accountDetector.browserProfileUpdated.connect(self._browserProfileUpdated)
        self.accountDetector.accountDetected.connect(self.accountDetected)
        self.accountDetector.errorOccurred.connect(self._errorOccurred)
        self.accountDetector.finished.connect(self._finished)
        self._importStarted: bool = False
        self._cancelRequested: bool = False
        self._browserInfo = browserInfo
        self._profiles = self.accountDetector.getProfiles(self._browserInfo)
        self._loadOptions()

    def _loadOptions(self) -> None:
        self._showInfoText(self._browserInfo.getDisplayName())
        if len(self._profiles) > 1:
            self._ui.profileSelectComboBox.addItem(T("detect-automatically"), userData=None)
            for profile in self._profiles:
                self._ui.profileSelectComboBox.addItem(f"[{profile.browserName}] {profile.displayName}", userData=profile)
            self._ui.contentArea.setCurrentIndex(0)
        else:
            self.importAccount()

    def importAccount(self) -> None:
        if self._importStarted:
            return
        self._importStarted = True
        self._ui.progressInfo.setText(T("loading", ellipsis=True))
        self._ui.contentArea.setCurrentIndex(1)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.accountDetector.importAccount(
            browserInfo=self._browserInfo,
            profile=self._ui.profileSelectComboBox.currentData()
        )

    def _showInfoText(self, browserName: str) -> None:
        self._ui.info.setText(T("#The Twitch account saved in your {browserName} browser will be detected and linked.\nSince {appName} shares the same account information as your browser, logging out of your Twitch account in the browser will also log you out of {appName}.\n\n\nBefore proceeding, please make sure that {browserName} is installed and that you are logged in to Twitch.\n\nAlso, please close all {browserName} windows and terminate any running {browserName} processes.", browserName=browserName, appName=Config.APP_NAME))

    def _browserProfileUpdated(self, browserProfile: BrowserProfile) -> None:
        if not self._cancelRequested:
            importInfoText = T("#Importing Twitch account from {browserName}", ellipsis=True, browserName=browserProfile.browserName)
            profileInfoText = f"{T("profile")}: {browserProfile.displayName}({browserProfile.key})"
            if len(self._profiles) > 1:
                self._ui.progressInfo.setText(f"{importInfoText}\n{profileInfoText}")
            else:
                self._ui.progressInfo.setText(importInfoText)

    def _errorOccurred(self, exception: Exception) -> None:
        self.errorOccurred.emit(self._browserInfo, exception)

    def _finished(self) -> None:
        super().accept()

    def accept(self) -> None:
        self.importAccount()

    def reject(self) -> None:
        if self._importStarted and not self._cancelRequested:
            self._cancelRequested = True
            self.accountDetector.abort()
            self._ui.progressInfo.setText(T("canceling", ellipsis=True))
            self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setEnabled(False)
        else:
            super().reject()