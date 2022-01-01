from Core.App import App
from Core.StatusCode import StatusCode
from Core.Updater import Updater
from Core.Ui import *
from Services.Messages import Messages
from Download.DownloadManager import DownloadManager

import os


class MainWindow(QtWidgets.QMainWindow, UiFile.mainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon(Config.ICON_IMAGE))
        self.setupMenuBar()
        self.tabWidget.tabBar().hide()
        self.tabWidget.tabCloseRequested.connect(self.closeTab)

    def start(self):
        Ui.Loading().exec()
        self.addTab(Ui.Home(), unclosable=True)
        self.show()
        self.onStartThread = Utils.WorkerThread()
        self.onStartThread.finished.connect(self.onStart)
        self.onStartThread.start()

    def onStart(self):
        self.showStatus()
        if Updater.status.isRunnable():
            if DB.termsOfService.getAgreedTime() == None:
                self.openTermsOfService()
        else:
            App.exit()

    def showStatus(self):
        status = Updater.status.getStatus()
        if status == Updater.status.CONNECTION_FAILURE:
            Utils.info(*Messages.INFO.SERVER_CONNECTION_FAILED)
        elif status == Updater.status.UNAVAILABLE:
            infoText = Updater.status.notice.message or T("#{appName} is currently unavailable.", appName=Config.APP_NAME)
            if Updater.status.notice.url == None:
                Utils.info("warning", infoText)
            else:
                if Utils.ask("warning", infoText, okText="details", cancelText="ok",  defaultOk=True):
                    Utils.openUrl(Updater.status.notice.url)
        elif status == Updater.status.AVAILABLE:
            if Updater.status.notice.message != None:
                if Updater.status.notice.url == None:
                    Utils.info("notice", Updater.status.notice.message)
                else:
                    if Utils.ask("notice", Updater.status.notice.message, okText="details", cancelText="ok",  defaultOk=True):
                        Utils.openUrl(Updater.status.notice.url)
        else:
            updateInfoTitle = T("#Optional update" if status == Updater.status.UPDATE_FOUND else "#Update required")
            updateInfoString = T("#A new version of {appName} has been released!", appName=Config.APP_NAME)
            if Updater.status.version.updateNote != None:
                updateInfoString = "{}\n\n\n{} {}\n\n{}".format(updateInfoString, Config.APP_NAME, Updater.status.version.latestVersion, Updater.status.version.updateNote)
            if Utils.ask(updateInfoTitle, updateInfoString, okText="update", cancelText="ok" if status == Updater.status.UPDATE_FOUND else "cancel", defaultOk=True):
                Utils.openUrl(Updater.status.version.updateUrl)

    def closeEvent(self, event):
        event.ignore()
        if DownloadManager.isDownloaderRunning():
            if Utils.ask(*(Messages.ASK.APP_EXIT if DownloadManager.isShuttingDown() else Messages.ASK.APP_EXIT_WHILE_DOWNLOADING)):
                Utils.wait("shutting-down", T("#Shutting down downloader", ellipsis=True), target=DownloadManager.removeAll).exec()
                self.shutdown()
        else:
            if Utils.ask(*Messages.ASK.APP_EXIT):
                self.shutdown()

    def shutdown(self):
        self.saveWindow()
        App.exit()

    def setupMenuBar(self):
        self.actionNewDownloader.triggered.connect(self.openNewDownloader)
        self.actionSettings.triggered.connect(self.openSettings)
        self.actionAccount.triggered.connect(self.openAccount)
        self.actionGettingStarted.triggered.connect(self.gettingStarted)
        self.actionAbout.triggered.connect(self.openAbout)
        self.actionTermsOfService.triggered.connect(self.openTermsOfService)
        self.actionDonate.triggered.connect(self.donate)
        for widgetType in [QtWidgets.QMenuBar, QtWidgets.QMenu, QtWidgets.QAction]:
            for widget in self.findChildren(widgetType):
                widget.setFont(Translator.getFont(widget.font()))

    def openNewDownloader(self):
        os.startfile(Config.APP_PATH)

    def openSettings(self, page=0):
        try:
            Ui.Settings(page).exec()
        except:
            Utils.info("error", "#An error occurred while loading settings.")
            DB.reset()

    def openAccount(self):
        while Ui.Account().exec() == StatusCode.RESTART:
            pass

    def gettingStarted(self):
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "help", params={"lang": DB.localization.getLanguage()}))

    def openAbout(self):
        Ui.About().exec()

    def openTermsOfService(self):
        Ui.TermsOfService().exec()

    def donate(self):
       Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": DB.localization.getLanguage()}))

    def showDownload(self, downloaderId):
        self.setCurrentTab(self.addTab(Ui.Download(downloaderId)))

    def addTab(self, ui, unclosable=False):
        index = self.tabWidget.addTab(ui, T(ui.windowTitle()))
        if unclosable:
            self.tabWidget.tabBar().setTabButton(index, 1, None)
        return index

    def setCurrentTab(self, index):
        self.tabWidget.setCurrentIndex(index)

    def closeTab(self, index):
        self.tabWidget.widget(index).close()