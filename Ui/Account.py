from Core.Ui import *
from Services.Messages import Messages
from Services.Account import TwitchAccount


class Account(QtWidgets.QWidget, UiFile.account):
    startLoginRequested = QtCore.pyqtSignal()
    cancelLoginRequested = QtCore.pyqtSignal()
    profileImageChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(Account, self).__init__(parent=parent)
        self.profileImage.setImageSizePolicy((50, 50), (300, 300))
        self.accountInfo.setText(T("#Log in and link the benefits of your Twitch account with {appName}.\n(Stream Ad-Free benefits, Subscriber-Only Stream access, Subscriber-Only Video access, Twitch Prime or Twitch Turbo benefits, etc.)", appName=CoreConfig.APP_NAME))
        self.alertIcon = Utils.setSvgIcon(self.alertIcon, Icons.ALERT_RED_ICON)
        self.loginButton.clicked.connect(self.login)
        self.continueButton.clicked.connect(self.startLoginRequested)
        self.cancelButton.clicked.connect(self.cancelLogin)
        self.logoutButton.clicked.connect(self.logout)
        self.refreshAccountButton.clicked.connect(self.refreshAccount)
        self.profileImage.imageChanged.connect(self.updateAccountImage)
        self.updateAccountThread = Utils.WorkerThread(target=DB.account.updateAccount, parent=self)
        self.updateAccountThread.resultSignal.connect(self.accountUpdateResult)
        DB.account._user.accountUpdated.connect(self.showAccount)

    def refreshAccount(self):
        self.accountMenu.setCurrentIndex(0)
        self.updateAccountImage()
        self.updateAccountThread.start()

    def accountUpdateResult(self, result):
        if not result.success:
            if isinstance(result.error, TwitchAccount.Exceptions.InvalidToken) or isinstance(result.error, TwitchAccount.Exceptions.UserNotFound):
                self.info(*Messages.INFO.LOGIN_EXPIRED)

    def showAccount(self):
        if DB.account.isUserLoggedIn():
            self.accountMenu.setCurrentIndex(2)
            self.profileImage.loadImage(filePath=Images.PROFILE_IMAGE, url=DB.account.getAccountData().profileImageURL, urlFormatSize=ImageSize.USER_PROFILE, refresh=True)
            self.account.setText(DB.account.getAccountData().displayName)
        else:
            self.accountMenu.setCurrentIndex(1)
            self.infoArea.hide()
            self.buttonArea.setCurrentIndex(0)
            self.profileImage.cancelImageRequest()
            self.updateAccountImage()

    def updateAccountImage(self, image=None):
        self.profileImageChanged.emit(image)

    def login(self):
        self.infoArea.show()
        self.buttonArea.setCurrentIndex(1)
        self.startLoginRequested.emit()

    def cancelLogin(self):
        if self.ask("cancel-login", "#Are you sure you want to cancel the login operation in progress?"):
            self.cancelLoginRequested.emit()

    def loginTabClosed(self):
        self.infoArea.hide()
        self.buttonArea.setCurrentIndex(0)

    def logout(self):
        if self.ask("logout", "#Are you sure you want to log out?"):
            DB.account.logout()