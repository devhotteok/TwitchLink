from Core.App import App
from Core.Ui import *


class About(QtWidgets.QDialog, UiFile.about):
    def __init__(self):
        super().__init__(parent=App.getActiveWindow())
        self.appLabel.setText(Config.APP_NAME)
        self.appInfoLabel.setText("{} {}".format(T("version"), Config.VERSION))
        self.copyrightInfoLabel.setText(Config.getCopyrightInfo())
        self.homepageButton.clicked.connect(self.openHomepage)
        self.contactInfoLabel.setText("{} : {}\n{} : {}".format(T("discord"), Config.CONTACT.DISCORD, T("email"), Config.CONTACT.EMAIL))
        self.donateInfoLabel.setText(T("#If you like the program, consider contributing to {appName}!", appName=Config.APP_NAME))
        self.donateButton.clicked.connect(self.openDonate)

    def openHomepage(self):
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, params={"lang": DB.localization.getLanguage()}))

    def openDonate(self):
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": DB.localization.getLanguage()}))