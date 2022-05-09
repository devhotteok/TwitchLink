from Core.Updater import Updater
from Core.Ui import *


class About(QtWidgets.QWidget, UiFile.about):
    def __init__(self, parent=None):
        super(About, self).__init__(parent=parent)
        self.appNameLabel.setText(Config.APP_NAME)
        self.appInfoLabel.setText(T("#Twitch Stream / Video / Clip Downloader"))
        self.versionInfoLabel.setText(f"{T('version')} {Config.VERSION}")
        if Config.VERSION == Updater.status.version.latestVersion:
            self.updateInfoLabel.setText(T("#This is the latest version."))
            self.updateInfoLabel.setStyleSheet("color: rgb(105, 105, 105);")
            self.updateButton.hide()
        else:
            self.updateInfoLabel.setText(T("#{appName} {version} has been released!", appName=Config.APP_NAME, version=Updater.status.version.latestVersion))
            self.updateInfoLabel.setStyleSheet("color: rgb(255, 0, 0);")
            self.updateButton.clicked.connect(self.openUpdate)
        self.copyrightInfoLabel.setText(Config.getCopyrightInfo())
        self.homepageButton.clicked.connect(self.openHomepage)
        self.contactInfoArea.layout().addRow(f"{T('discord')}:", QtWidgets.QLabel(Config.CONTACT.DISCORD, parent=self))
        self.contactInfoArea.layout().addRow(f"{T('email')}:", QtWidgets.QLabel(Config.CONTACT.EMAIL, parent=self))
        self.sponsorInfoLabel.setText(T("#If you like the program, please become a patron of {appName}!", appName=Config.APP_NAME))
        self.sponsorButton.clicked.connect(self.openSponsor)

    def openHomepage(self):
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, params={"lang": DB.localization.getLanguage()}))

    def openSponsor(self):
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": DB.localization.getLanguage()}))

    def openUpdate(self):
        Utils.openUrl(Utils.joinUrl(Updater.status.version.updateUrl, params={"lang": DB.localization.getLanguage()}))