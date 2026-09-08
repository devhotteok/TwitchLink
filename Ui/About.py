from Core.Ui import *


class About(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("about", self)
        self._ui.appNameLabel.setText(Config.APP_NAME)
        self._ui.updateButton.clicked.connect(self.openUpdate)
        self._ui.copyrightInfoLabel.setText(Config.getCopyrightInfo())
        self._ui.homepageButton.clicked.connect(self.openHomepage)
        if len(Config.CONTACT) == 0:
            self._ui.line_2.hide()
            self._ui.contactLabel.hide()
            self._ui.contactInfoArea.hide()
        else:
            for key, value in Config.CONTACT.items():
                self._ui.contactInfoArea.layout().addRow(f"{key}:", QtWidgets.QLabel(value, parent=self))
        self._ui.sponsorButton.clicked.connect(self.openSponsor)
        App.Updater.statusUpdated.connect(self.showVersionInfo)
        self.retranslateDynamicUi()

    def showVersionInfo(self) -> None:
        self._ui.versionInfoLabel.setText(f"{T('ui.version')} {Config.APP_VERSION}")
        if App.Updater.status.versionInfo.hasUpdate():
            self._ui.updateInfoLabel.setText(T("messages.#_has_been_released", appName=Config.APP_NAME, version=App.Updater.status.versionInfo.latestVersion))
            self._ui.updateInfoLabel.setStyleSheet("color: rgb(255, 0, 0);")
            self._ui.updateButton.show()
        else:
            self._ui.updateInfoLabel.setText(T("messages.#this_is_latest_version"))
            self._ui.updateInfoLabel.setStyleSheet("color: rgb(105, 105, 105);")
            self._ui.updateButton.hide()

    def openHomepage(self) -> None:
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, params={"lang": App.Translator.getCurrentLanguageCode()}))

    def openSponsor(self) -> None:
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": App.Translator.getCurrentLanguageCode()}))

    def openUpdate(self) -> None:
        Utils.openUrl(Utils.joinUrl(App.Updater.status.versionInfo.updateUrl, params={"lang": App.Translator.getCurrentLanguageCode()}))

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)
            self.retranslateDynamicUi()

    def retranslateDynamicUi(self) -> None:
        self._ui.appInfoLabel.setText(T("messages.#twitch_stream_video_clip_downloader"))
        self._ui.sponsorInfoLabel.setText(T("messages.#if_you_like_program_please_become_patro", appName=Config.APP_NAME))
        self.showVersionInfo()
