from Core.Ui import *
from Services.Account.AccountData import AccountData
from Services.Account.ExternalBrowserDriver import ExternalBrowserDriver, BrowserInfo


class ExternalBrowserLauncher(QtWidgets.QDialog):
    accountDetected = QtCore.pyqtSignal(AccountData)
    errorOccurred = QtCore.pyqtSignal(BrowserInfo)

    def __init__(self, browserInfo: BrowserInfo, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("externalBrowserLauncher", self)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowCloseButtonHint, False)
        self._externalBrowserDriver = ExternalBrowserDriver(logger=App.Instance.logger, parent=self)
        self._externalBrowserDriver.accountDetected.connect(self.accountDetected)
        self._externalBrowserDriver.errorOccurred.connect(self.errorOccurred)
        self._externalBrowserDriver.finished.connect(self._finished)
        self._externalBrowserDriver.launch(browserInfo=browserInfo)
        self._cancelRequested: bool = False
        self._ui.info.setText(T("#{browserName} has been launched. Please proceed with the sign-in process.", browserName=browserInfo.getDisplayName()))

    def _finished(self) -> None:
        self.accept()

    def reject(self) -> None:
        if not self._cancelRequested:
            self._cancelRequested = True
            self._externalBrowserDriver.abort()
            self._ui.progressInfo.setText(T("canceling", ellipsis=True))
            self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setEnabled(False)