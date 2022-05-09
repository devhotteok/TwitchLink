from Core.Ui import *
from Services.Messages import Messages
from Services.Account import Auth


class Account(QtWidgets.QWidget, UiFile.account):
    profileImageChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(Account, self).__init__(parent=parent)
        self.profile_image.setImageSizePolicy((50, 50), (300, 300))
        self.loginButton.clicked.connect(self.login)
        self.logoutButton.clicked.connect(self.logout)
        self.refreshAccountButton.clicked.connect(self.refreshAccount)
        self.profile_image.imageChanged.connect(self.updateAccountImage)
        self.thread = Utils.WorkerThread(parent=self)

    def refreshAccount(self):
        self.accountMenu.setCurrentIndex(0)
        self.updateAccountImage()
        self.thread.setup(target=DB.account.updateAccount, disconnect=True)
        self.thread.resultSignal.connect(self.accountUpdateResult)
        self.thread.start()

    def accountUpdateResult(self, result):
        self.showAccount()
        if not result.success:
            if isinstance(result.error, Auth.Exceptions.InvalidToken) or isinstance(result.error, Auth.Exceptions.UserNotFound):
                self.info(*Messages.INFO.LOGIN_EXPIRED)

    def showAccount(self):
        if DB.account.isUserLoggedIn():
            self.accountMenu.setCurrentIndex(2)
            self.profile_image.loadImage(filePath=Images.PROFILE_IMAGE, url=DB.account.getAccountData().profileImageURL, urlFormatSize=ImageSize.USER_PROFILE, refresh=True)
            self.account.setText(DB.account.getAccountData().displayName)
        else:
            self.accountMenu.setCurrentIndex(1)
            self.loginInfo.hide()
            self.profile_image.cancelImageRequest()
            self.updateAccountImage()
            self.loginButton.setAutoDefault(True)

    def updateAccountImage(self, image=None):
        self.profileImageChanged.emit(image or Icons.ACCOUNT_ICON)

    def login(self):
        self.setEnabled(False)
        self.loginInfo.show()
        self.loginButton.setText(T("#Logging in", ellipsis=True))
        self.thread.setup(target=DB.account.login, disconnect=True)
        self.thread.resultSignal.connect(self.loginResult)
        self.thread.start()

    def loginResult(self, result):
        self.setEnabled(True)
        self.loginInfo.hide()
        self.loginButton.setText(T("login"))
        if result.success:
            self.showAccount()
        elif isinstance(result.error, Auth.Exceptions.BrowserNotFound):
            self.info("error", "#Chrome browser or Edge browser is required to proceed.")
        elif isinstance(result.error, Auth.Exceptions.BrowserNotLoadable):
            self.info("error", "#Unable to load Chrome browser or Edge browser.\nIf the error persists, try Run as administrator.")
        else:
            self.info("error", "#Login failed.")

    def logout(self):
        if self.ask("logout", "#Are you sure you want to log out?"):
            DB.account.logout()
            self.showAccount()