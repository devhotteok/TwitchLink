from Core.App import App
from Core.StatusCode import StatusCode
from Core.Ui import *
from Services.Messages import Messages
from Services.Account import Auth


class Account(QtWidgets.QDialog, UiFile.account):
    def __init__(self):
        super().__init__(parent=App.getActiveWindow())
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowCloseButtonHint)
        self.accountUpdateThread = Utils.WorkerThread(target=DB.account.updateAccount)
        self.accountUpdateThread.resultSignal.connect(self.accountUpdateResult)
        self.accountUpdateThread.start()

    def accountUpdateResult(self, result):
        if DB.account.isUserLoggedIn():
            self.accountMenu.setCurrentIndex(2)
            self.profile_image.setImageSizePolicy((50, 50), (300, 300))
            self.profileImageLoader = Utils.ImageLoader(self.profile_image, DB.account.getAccountData().profileImageURL, Config.PROFILE_IMAGE)
            self.account.setText(DB.account.getAccountData().displayName)
            self.logoutButton.clicked.connect(self.logout)
        else:
            self.accountMenu.setCurrentIndex(1)
            self.loginInfo.hide()
            self.loginButton.clicked.connect(self.login)
            self.loginButton.setAutoDefault(True)
        if not result.success:
            if result.error == Auth.Exceptions.InvalidToken or result.error == Auth.Exceptions.UserNotFound:
                Utils.info(*Messages.INFO.LOGIN_EXPIRED)

    def login(self):
        self.setEnabled(False)
        self.loginInfo.show()
        self.loginButton.setText(T("#Logging in", ellipsis=True))
        self.loginThread = Utils.WorkerThread(target=DB.account.login)
        self.loginThread.resultSignal.connect(self.loginResult)
        self.loginThread.start()

    def loginResult(self, result):
        self.setEnabled(True)
        self.loginInfo.hide()
        self.loginButton.setText(T("login"))
        if result.success:
            self.restart()
        elif result.error == Auth.Exceptions.BrowserNotFound:
            Utils.info("error", "#Chrome browser or Edge browser is required to proceed.")
        elif result.error == Auth.Exceptions.BrowserNotLoadable:
            Utils.info("error", "#Unable to load Chrome browser or Edge browser.\nIf the error persists, try Run as administrator.")
        else:
            Utils.info("error", "#Login failed.")

    def logout(self):
        if Utils.ask("logout", "#Are you sure you want to log out?"):
            DB.account.logout()
            self.restart()

    def closeEvent(self, event):
        if self.isEnabled():
            return super().closeEvent(event)
        else:
            return event.ignore()

    def restart(self):
        self.accept(StatusCode.RESTART)