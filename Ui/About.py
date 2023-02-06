from Core.Updater import Updater
from Core.Ui import *


class About(QtWidgets.QWidget, UiFile.about):
    def __init__(self, parent=None):
        super(About, self).__init__(parent=parent)
        self.appNameLabel.setText(Config.APP_NAME)
        self.appInfoLabel.setText(T("#Twitch Stream / Video / Clip Downloader"))
        self.updateButton.clicked.connect(self.openUpdate)
        self.copyrightInfoLabel.setText(Config.getCopyrightInfo())
        self.homepageButton.clicked.connect(self.openHomepage)
        for key, value in Config.CONTACT.items():
            self.contactInfoArea.layout().addRow(f"{key}:", QtWidgets.QLabel(value, parent=self))
        self.sponsorInfoLabel.setText(T("#If you like the program, please become a patron of {appName}!", appName=Config.APP_NAME))
        self.sponsorButton.clicked.connect(self.openSponsor)
        Updater.statusUpdated.connect(self.showVersionInfo)
        self.showVersionInfo()

    def showVersionInfo(self):
        self.versionInfoLabel.setText(f"{T('version')} {Config.APP_VERSION}")
        if Config.APP_VERSION == Updater.status.version.latestVersion:
            self.updateInfoLabel.setText(T("#This is the latest version."))
            self.updateInfoLabel.setStyleSheet("color: rgb(105, 105, 105);")
            self.updateButton.hide()
        else:
            self.updateInfoLabel.setText(T("#{appName} {version} has been released!", appName=Config.APP_NAME, version=Updater.status.version.latestVersion))
            self.updateInfoLabel.setStyleSheet("color: rgb(255, 0, 0);")
            self.updateButton.show()

    def openHomepage(self):
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, params={"lang": Translator.getLanguage()}))

    def openSponsor(self):
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": Translator.getLanguage()}))

    def openUpdate(self):
        Utils.openUrl(Utils.joinUrl(Updater.status.version.updateUrl, params={"lang": Translator.getLanguage()}))