import os
import sys
import gc

from PyQt5.QtCore import QLibraryInfo, QTranslator, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QAction

from TwitchLinkUi import Ui, UiFiles
from TwitchLinkConfig import Config

from Services.Twitch.TwitchGqlAPI import TwitchGqlAPI
from Services.TwitchLinkUtils import Utils
from Services.TwitchLinkDataBase import DataBase
from Services.TwitchLinkTranslator import translator, T


class TwitchLink(QMainWindow, UiFiles.mainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = DataBase()
        self.loadTranslators()
        self.ui = Ui(self.db)
        self.db.setUi(self.ui)
        self.db.setApp(app)
        self.db.setMainWindow(self)
        self.Loading = self.db.ui.Loading()
        self.Loading.show()
        self.db.checkStatus()
        self.db.setApi(TwitchGqlAPI())
        self.setupUi(self)
        self.setWindowIcon(QIcon(Config.ICON_IMAGE))
        self.setupMenuBar()
        self.startMainMenu()
        self.Loading.close()
        self.show()
        self.onStartThread = OnStart()
        self.onStartThread.signal.connect(self.onStart)
        self.onStartThread.start()

    def loadTranslators(self):
        self.translators = []
        language = translator.getLanguage()
        path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        for fileName in ["qt_{}", "qtbase_{}"]:
            defaultTranslator = QTranslator(self.app)
            defaultTranslator.load(fileName.format(language), path)
            self.translators.append(defaultTranslator)
            app.installTranslator(defaultTranslator)
        for ui in UiFiles.TRANSLATION_LIST:
            customTranslator = QTranslator(self.app)
            customTranslator.load(ui, Config.TRANSLATORS_PATH + "/" + language)
            self.translators.append(customTranslator)
            app.installTranslator(customTranslator)

    def removeTranslators(self):
        for translator in self.translators:
            self.app.removeTranslator(translator)

    def onStart(self):
        if self.checkStatus():
            if self.db.setup.termsOfServiceAgreedTime == None:
                self.openTermsOfService()
        else:
            self.db.forceClose()

    def checkStatus(self):
        status = self.db.programStatus
        if status == "Server Error":
            Utils.info("error", "#A temporary error occurred while connecting to the server.\nPlease try again later.")
        elif status == "Unavailable":
            if self.db.statusMessage == None:
                Utils.info("warning", "#{name} is currently unavailable.", name=T("#PROGRAM_NAME"))
            else:
                Utils.info("warning", "#{name} is currently unavailable.\n{message}", name=T("#PROGRAM_NAME"), message=self.db.statusMessage)
        elif status == "Available":
            if self.db.serverNotice != None:
                Utils.info("notice", self.db.serverNotice)
            return True
        else:
            if self.db.updateNote == None:
                updateInfoString = "#A new version of {name} has been released!\n\n* {updateType}"
            else:
                updateInfoString = "#A new version of {name} has been released!\n{updateNote}\n\n* {updateType}"
            if status == "Update Found":
                if Utils.ask("update-notice", updateInfoString, "update", "ok", True, name=T("#PROGRAM_NAME"), updateNote=self.db.updateNote, updateType=T("#Optional update")):
                    QDesktopServices.openUrl(QUrl(self.db.updateUrl))
                return True
            elif status == "Update Required":
                if Utils.ask("update-notice", updateInfoString, "update", "cancel", True, name=T("#PROGRAM_NAME"), updateNote=self.db.updateNote, updateType=T("#Update required")):
                    QDesktopServices.openUrl(QUrl(self.db.updateUrl))
        return False

    def closeEvent(self, event):
        if self.db.forcedClose:
            return
        if self.db.downloading:
            if Utils.ask("warning", "#There is a download in progress.\nDo you want to cancel and exit?"):
                self.Download.downloader.cancelDownload()
            else:
                event.ignore()
        else:
            if not Utils.ask("notification", "#Are you sure you want to exit?"):
                event.ignore()

    def setWindow(self, ui):
        self.setWindowTitle(T(ui.windowTitle()))
        self.setCentralWidget(ui)
        gc.collect()
        if Config.SHOW_ADS:
            self.setFixedSize(ui.size())
        else:
            self.setFixedSize(ui.width() - ui.adSize[0], ui.height() - ui.adSize[1])
        self.setFont(translator.getFont())

    def setupMenuBar(self):
        self.actionNewDownloader.triggered.connect(self.openNewDownloader)
        self.actionChannel.triggered.connect(lambda: self.startSearch("channel_id"))
        self.actionVideoClip.triggered.connect(lambda: self.startSearch("video_id"))
        self.actionUrl.triggered.connect(lambda: self.startSearch("video_url"))
        self.actionSettings.triggered.connect(self.openSettings)
        self.actionLogin.triggered.connect(self.openLogin)
        self.actionAbout.triggered.connect(self.openAbout)
        self.actionTermsOfService.triggered.connect(self.openTermsOfService)
        self.actionDonate.triggered.connect(self.donate)
        for widget in self.findChildren(QMenuBar) + self.findChildren(QMenu) + self.findChildren(QAction):
            widget.setFont(translator.getFont(widget.font()))

    def openNewDownloader(self):
        os.startfile(Config.PROGRAM_PATH)

    def openSettings(self):
        try:
            self.Settings = self.ui.Settings()
            self.Settings.exec()
            del self.Settings
            gc.collect()
        except:
            Utils.info("error", "#An error occurred while loading settings.")
            self.db.resetSettings()

    def openLogin(self):
        self.Login = self.ui.Login()
        self.Login.exec()
        del self.Login
        gc.collect()

    def openAbout(self):
        self.About = self.ui.About()
        self.About.exec()
        del self.About
        gc.collect()

    def openTermsOfService(self):
        self.TermsOfService = self.ui.TermsOfService()
        self.TermsOfService.exec()
        del self.TermsOfService
        gc.collect()

    def donate(self):
        QDesktopServices.openUrl(QUrl(Config.HOMEPAGE_URL + "/donate?lang=" + self.db.localization.language))

    def startMainMenu(self):
        self.MainMenu = self.ui.MainMenu()
        self.setWindow(self.MainMenu)
        self.menuSearch.setEnabled(True)
        self.mainMenuLoading(False)

    def startSearch(self, mode):
        self.Search = self.ui.Search(mode)
        if self.Search.exec():
            if mode == "channel_id" and len(self.db.settings.bookmarks) != 0:
                self.searchData(mode, self.Search.queryComboBox.currentText().strip())
            else:
                self.searchData(mode, self.Search.query.text().strip())
        del self.Search
        gc.collect()

    def mainMenuLoading(self, message):
        if message == False:
            self.MainMenu.info.setText(T("#Search By"))
            self.MainMenu.menuArea.show()
        else:
            self.MainMenu.info.setText(T(message))
            self.MainMenu.menuArea.hide()
        self.repaint()

    def searchData(self, mode, query):
        if query == "":
            Utils.info("no-results-found", "#Well.. You forgot to type your keyword!")
            return
        if mode == "video_id":
            if not query.isnumeric():
                mode = "clip_id"
        elif mode == "video_url":
            self.mainMenuLoading("#Checking link...")
            mode, query = Utils.parseTwitchUrl(query)
            if mode == None:
                self.mainMenuLoading(False)
                Utils.info("no-results-found", "#Oops! Wrong link!")
                return
        if mode == "channel_id":
            self.mainMenuLoading("#Checking channel info...")
            try:
                channel = self.db.api.getChannel(query)
            except:
                self.mainMenuLoading(False)
                Utils.info("no-results-found", "#Channel not found.")
                return
            data = {"channel": channel}
        elif mode == "video_id":
            self.mainMenuLoading("#Checking video info...")
            try:
                video = self.db.api.getVideo(query)
            except:
                self.mainMenuLoading(False)
                Utils.info("no-results-found", "#Video not found.")
                return
            data = {"video": video}
        else:
            self.mainMenuLoading("#Checking clip info...")
            try:
                clip = self.db.api.getClip(query)
            except:
                self.mainMenuLoading(False)
                Utils.info("no-results-found", "#Clip not found.")
                return
            data = {"clip": clip}
        self.startVideoList(mode, data)

    def startVideoList(self, mode, data):
        self.mainMenuLoading("#Loading data...")
        self.VideoList = self.ui.VideoList(mode, data)
        self.mainMenuLoading(False)
        self.VideoList.exec()
        del self.VideoList
        gc.collect()
        if self.db.checkDownload():
            self.startDownload()

    def startDownload(self):
        self.Download = self.ui.Download()
        self.setWindow(self.Download)
        self.menuSearch.setEnabled(False)

class OnStart(QThread):
    signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        self.signal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    while True:
        program = TwitchLink(app)
        returnCode = app.exec()
        if returnCode != -1:
            break
        program.removeTranslators()
        del program
        gc.collect()
    sys.exit(returnCode)