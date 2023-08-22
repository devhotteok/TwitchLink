from Core.Ui import *
from Services.Messages import Messages
from Services.Document import DocumentData, DocumentButtonData
from Ui.Components.Operators.NavigationBar import NavigationBar
from Ui.Components.Pages.SearchPage import SearchPage
from Ui.Components.Pages.DownloadsPage import DownloadsPage
from Ui.Components.Pages.ScheduledDownloadsPage import ScheduledDownloadsPage
from Ui.Components.Pages.AccountPage import AccountPage
from Ui.Components.Pages.InformationPage import InformationPage

from PyQt6.QtWebEngineWidgets import QWebEngineView


class MainWindow(QtWidgets.QMainWindow, WindowGeometryManager):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("mainWindow", self)
        self._webViewEnabled = False
        App.Instance.appStarted.connect(self.start, QtCore.Qt.ConnectionType.QueuedConnection)
        App.Instance.newInstanceStarted.connect(self.activate)

    def start(self) -> None:
        if App.Preferences.setup.needSetup():
            if Ui.Setup().exec():
                App.Instance.restart()
            else:
                App.Instance.exit()
        else:
            loading = Ui.Loading()
            loading.completeSignal.connect(self.onLoadingComplete)
            loading.exec()
            self.show()

    def onLoadingComplete(self) -> None:
        self.loadWindowGeometry()
        self.loadComponents()
        self.setupSystemTray()
        self.setup()

    def loadComponents(self) -> None:
        self.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        self._ui.actionGettingStarted.triggered.connect(self.gettingStarted)
        self._ui.actionAbout.triggered.connect(self.openAbout)
        self._ui.actionTermsOfService.triggered.connect(self.openTermsOfService)
        self._ui.actionSponsor.triggered.connect(self.sponsor)
        self.navigationBar = NavigationBar(self._ui.navigationArea, parent=self)
        self.navigationBar.focusChanged.connect(self.onFocusChange)
        self.searchPageObject = self.navigationBar.addPage(self._ui.searchPageButton, self._ui.searchPage, icon=QtGui.QIcon(Icons.SEARCH_ICON))
        self.downloadsPageObject = self.navigationBar.addPage(self._ui.downloadsPageButton, self._ui.downloadsPage, icon=QtGui.QIcon(Icons.DOWNLOAD_ICON))
        self.scheduledDownloadsPageObject = self.navigationBar.addPage(self._ui.scheduledDownloadsPageButton, self._ui.scheduledDownloadsPage, icon=QtGui.QIcon(Icons.SCHEDULED_ICON))
        self.accountPageObject = self.navigationBar.addPage(self._ui.accountPageButton, self._ui.accountPage, icon=QtGui.QIcon(Icons.ACCOUNT_ICON))
        self.settingsPageObject = self.navigationBar.addPage(self._ui.settingsPageButton, self._ui.settingsPage, icon=QtGui.QIcon(Icons.SETTINGS_ICON))
        self.informationPageObject = self.navigationBar.addPage(self._ui.informationPageButton, self._ui.informationPage, icon=QtGui.QIcon(Icons.INFO_ICON))
        self.search = SearchPage(self.searchPageObject, parent=self)
        self.search.accountPageShowRequested.connect(self.accountPageObject.show)
        self._ui.searchPage.layout().addWidget(self.search)
        self.downloads = DownloadsPage(self.downloadsPageObject, parent=self)
        self.downloads.accountPageShowRequested.connect(self.accountPageObject.show)
        self.downloads.appShutdownRequested.connect(self.shutdown)
        self.downloads.systemShutdownRequested.connect(self.shutdownSystem)
        self._ui.downloadsPage.layout().addWidget(self.downloads)
        self.scheduledDownloads = ScheduledDownloadsPage(self.scheduledDownloadsPageObject, parent=self)
        self._ui.scheduledDownloadsPage.layout().addWidget(self.scheduledDownloads)
        self.account = AccountPage(self.accountPageObject, parent=self)
        self._ui.accountPage.layout().addWidget(self.account)
        self.settings = Ui.Settings(parent=self)
        self.settings.restartRequired.connect(self.restart)
        self._ui.settingsPage.layout().addWidget(self.settings)
        self.information = InformationPage(self.informationPageObject, parent=self)
        self.information.termsOfServiceAccepted.connect(self._termsOfServiceAccepted)
        self.information.appShutdownRequested.connect(self.shutdown)
        self._ui.informationPage.layout().addWidget(self.information)

    def setupSystemTray(self) -> None:
        contextMenu = App.Instance.systemTrayIcon.contextMenu()
        self.openAppAction = QtGui.QAction(T("open"), parent=contextMenu)
        self.closeAppAction = QtGui.QAction(T("exit"), parent=contextMenu)
        self.openAppAction.triggered.connect(self.activate)
        self.closeAppAction.triggered.connect(self.close)
        contextMenu.addAction(self.openAppAction)
        contextMenu.addAction(self.closeAppAction)
        App.Instance.systemTrayIcon.clicked.connect(self.activate)

    def setup(self) -> None:
        self.statusUpdated(isInSetup=True)
        if App.Updater.status.isOperational():
            if App.Preferences.setup.getTermsOfServiceAgreement() == None:
                self.openTermsOfService()
            else:
                self._termsOfServiceAccepted()
            App.Updater.statusUpdated.connect(self.statusUpdated)
            App.Updater.startAutoUpdate()
            App.GlobalDownloadManager.statsUpdated.connect(self.showContributeInfo, QtCore.Qt.ConnectionType.QueuedConnection)
        if Utils.isFile(Config.TRACEBACK_FILE):
            file = QtCore.QFile(Config.TRACEBACK_FILE, self)
            if file.open(QtCore.QIODevice.OpenModeFlag.ReadOnly):
                fileName = file.readAll().data().decode()
                self.information.showAppInfo(
                    DocumentData(
                        contentId="CRASH_REPORT",
                        title=T("#{appName} has crashed.", appName=Config.APP_NAME),
                        content=T("#{appName} has crashed due to an unexpected error.\nIf this happens frequently, please attach the following log file and report it to us.\n\nFile: {fileName}", appName=Config.APP_NAME, fileName=fileName),
                        contentType="text",
                        modal=True,
                        buttons=[
                            DocumentButtonData(text=T("ok"), role="accept", default=True),
                            DocumentButtonData(text=T("open-file"), action=f"file:{fileName}", role="action", default=False),
                            DocumentButtonData(text=T("report-error"), action=f"url:{Config.HOMEPAGE_URL}", role="action", default=False)
                        ]
                    )
                )
            file.remove()
            file.deleteLater()

    def _termsOfServiceAccepted(self) -> None:
        self.account.refreshAccount()
        App.Account.updateIntegrityToken()

    def show(self) -> None:
        if self._webViewEnabled:
            super().show()
        else:
            webView = QWebEngineView(parent=self)
            webView.load(QtCore.QUrl())
            webView.deleteLater()
            self._webViewEnabled = True
            super().show()

    def statusUpdated(self, isInSetup: bool = False) -> None:
        isOperational = App.Updater.status.isOperational()
        allowPageView = not isInSetup
        self.menuBar().setEnabled(isOperational or allowPageView)
        if not isOperational and allowPageView:
            self.downloadsPageObject.focus()
            self.scheduledDownloadsPageObject.focus()
            self.settingsPageObject.focus()
        else:
            self.downloadsPageObject.unfocus()
            self.scheduledDownloadsPageObject.unfocus()
            self.settingsPageObject.unfocus()
        App.GlobalDownloadManager.setDownloaderCreationEnabled(isOperational)
        if isInSetup:
            App.ScheduledDownloadManager.setBlocked(not isOperational)
        contentId = "APP_STATUS"
        self.information.removeAppInfo(contentId)
        status = App.Updater.status.getStatus()
        if status == App.Updater.status.Types.CONNECTION_FAILURE:
            if isInSetup:
                content = T("#Please try again later.")
                buttons = [
                    DocumentButtonData(text=T("ok"), action=self.shutdown, role="action", default=True)
                ]
            else:
                content = T("#Some features will be temporarily disabled.\nPlease wait.\nWhen the connection is restored, those features will be activated.")
                buttons = []
            self.information.showAppInfo(
                DocumentData(
                    contentId=contentId,
                    title=T("network-error"),
                    content=f"{T('#A network error occurred while connecting to the server.')}\n{content}",
                    contentType="text",
                    modal=True,
                    buttons=buttons
                )
            )
        elif status == App.Updater.status.Types.UNEXPECTED_ERROR:
            App.Updater.stopAutoUpdate()
            if isInSetup:
                content = T("#Please try again later.")
                buttons = [
                    DocumentButtonData(text=T("ok"), action=self.shutdown, role="action", default=True)
                ]
            else:
                content = f"{T('#Some features will be disabled.')}\n{T('#Please restart the app.')}"
                buttons = []
            self.information.showAppInfo(
                DocumentData(
                    contentId=contentId,
                    title=T("error"),
                    content=f"{T('#An unexpected error occurred while connecting to the server.')}\n{content}",
                    contentType="text",
                    modal=True,
                    buttons=buttons
                )
            )
        elif status == App.Updater.status.Types.SESSION_EXPIRED:
            App.Updater.stopAutoUpdate()
            self.information.showAppInfo(
                DocumentData(
                    contentId=contentId,
                    title=T("session-expired"),
                    content=f"{T('#Your session has expired.')}\n{T('#Some features will be disabled.')}\n{T('#Please restart the app.')}",
                    contentType="text",
                    modal=True,
                    buttons=[]
                )
            )
        elif status == App.Updater.status.Types.UNAVAILABLE:
            self.information.showAppInfo(
                DocumentData(
                    contentId=contentId,
                    title=T("service-unavailable"),
                    content=App.Updater.status.operationalInfo or T("#{appName} is currently unavailable.", appName=Config.APP_NAME),
                    contentType=App.Updater.status.operationalInfoType or "text",
                    modal=True,
                    buttons=[DocumentButtonData(text=T("ok"), action=self.shutdown, role="action", default=True)] if isInSetup else []
                )
            )
            if not isInSetup:
                self.restart()
        elif status == App.Updater.status.Types.UPDATE_REQUIRED or status == App.Updater.status.Types.UPDATE_FOUND:
            if status == App.Updater.status.Types.UPDATE_REQUIRED:
                App.Updater.stopAutoUpdate()
            self.information.showAppInfo(
                DocumentData(
                    contentId=contentId,
                    title=T("recommended-update" if status == App.Updater.status.Types.UPDATE_FOUND else "required-update"),
                    content=App.Updater.status.versionInfo.updateNote or f"{T('#A new version of {appName} has been released!', appName=Config.APP_NAME)}\n\n[{Config.APP_NAME} {App.Updater.status.versionInfo.latestVersion if App.Updater.status.versionInfo.hasUpdate() else T('unknown')}]",
                    contentType=App.Updater.status.versionInfo.updateNoteType if App.Updater.status.versionInfo.updateNote else "text",
                    modal=status == App.Updater.status.Types.UPDATE_REQUIRED,
                    buttons=[
                        DocumentButtonData(text=T("update"), action=self.confirmUpdateShutdown, role="action", default=True),
                        DocumentButtonData(text=T("cancel"), action=(self.shutdown if isInSetup else self.confirmShutdown) if status == App.Updater.status.Types.UPDATE_REQUIRED else None, role="reject", default=False)
                    ]
                ),
                icon=Icons.UPDATE_FOUND_ICON
            )

    def onFocusChange(self, focus: bool) -> None:
        enabled = not focus
        self._ui.actionAbout.setEnabled(enabled)
        self._ui.actionTermsOfService.setEnabled(enabled)
        if focus:
            self.activate()

    def showContributeInfo(self, totalFiles: int, totalByteSize: int) -> None:
        if Utils.ask("contribute", T("#You have downloaded a total of {totalFiles}({totalSize}) videos so far.\nPlease become a patron of {appName} for better functionality and service.", totalFiles=totalFiles, totalSize=Utils.formatByteSize(totalByteSize), appName=Config.APP_NAME), contentTranslate=False, defaultOk=True, parent=self):
            Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": App.Translator.getLanguage()}))

    def confirmShutdown(self) -> None:
        if App.GlobalDownloadManager.isDownloaderRunning() and not App.GlobalDownloadManager.isShuttingDown():
            if Utils.ask(*Messages.ASK.STOP_CANCEL_ALL_DOWNLOADS, parent=self):
                self.shutdown()
        else:
            self.shutdown()

    def confirmUpdateShutdown(self) -> None:
        if App.GlobalDownloadManager.isDownloaderRunning() and not App.GlobalDownloadManager.isShuttingDown():
            if not Utils.ask(*Messages.ASK.STOP_CANCEL_ALL_DOWNLOADS, parent=self):
                return
        Utils.openUrl(Utils.joinUrl(App.Updater.status.versionInfo.updateUrl, params={"lang": App.Translator.getLanguage()}))
        self.shutdown()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        super().closeEvent(event)
        event.ignore()
        if App.Updater.status.isOperational() and self.isVisible() and App.Preferences.general.isSystemTrayEnabled() and event.spontaneous():
            self.moveToSystemTray()
        else:
            self.confirmShutdown()

    def gettingStarted(self) -> None:
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "help", params={"lang": App.Translator.getLanguage()}))

    def openAbout(self) -> None:
        self.information.openAbout()

    def openTermsOfService(self) -> None:
        self.information.openTermsOfService()

    def sponsor(self) -> None:
        Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": App.Translator.getLanguage()}))

    def waitForCleanup(self) -> None:
        if App.GlobalDownloadManager.isDownloaderRunning():
            msg = QtWidgets.QProgressDialog(parent=self)
            msg.setWindowTitle(T("shutting-down"))
            msg.setLabelText(T("#Shutting down all downloads" if App.GlobalDownloadManager.isDownloaderRunning() else "shutting-down", ellipsis=True))
            msg.setRange(0, 0)
            msg.setCancelButton(None)
            App.GlobalDownloadManager.cancelAll()
            App.GlobalDownloadManager.allCompletedSignal.connect(msg.close)
            msg.exec()

    def restart(self) -> None:
        self.shutdown(restart=True)

    def shutdown(self, restart: bool = False) -> None:
        App.Updater.stopAutoUpdate()
        App.Updater.status.setStatus(App.Updater.status.Types.NONE)
        App.Notifications.clearAll()
        App.GlobalDownloadManager.setDownloaderCreationEnabled(False)
        App.ScheduledDownloadManager.setBlocked(True)
        self.downloads.setScheduledShutdown(None)
        self.waitForCleanup()
        self.saveWindowGeometry()
        if restart:
            App.Instance.restart()
        else:
            App.Instance.exit()

    def shutdownSystem(self) -> None:
        self.shutdown()
        Utils.shutdownSystem(message=T("#Shutdown by {appName}'s scheduled task.", appName=Config.APP_NAME))

    def moveToSystemTray(self) -> None:
        if not self.isHidden():
            self.hide()
            App.Instance.notification.toastMessage(
                title=T("#Minimized to system tray"),
                message=T("#{appName} is running in the background.", appName=Config.APP_NAME),
                icon=App.Instance.notification.Icons.Information
            )

    def activate(self) -> None:
        if self.isHidden():
            self.show()
        self.setWindowState((self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized) | QtCore.Qt.WindowState.WindowActive)
        self.activateWindow()