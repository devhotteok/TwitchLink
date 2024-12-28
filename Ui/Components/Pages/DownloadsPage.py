from Core.Ui import *
from Ui.Components.Operators.NavigationBar import PageObject
from Ui.Components.Operators.TabManager import TabManager
from Ui.Components.Widgets.TimedMessageBox import TimedMessageBox

import enum
import uuid


class ScheduledShutdownTypes(enum.Enum):
    NONE = 0
    SHUTDOWN_APP = 1
    SHUTDOWN_SYSTEM = 2


class DownloadsPage(TabManager):
    accountPageShowRequested = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()
    systemShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, pageObject: PageObject, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.pageObject = pageObject
        self.downloads = Ui.Downloads(parent=self)
        self.downloads.accountPageShowRequested.connect(self.accountPageShowRequested)
        self.downloads.progressWindowRequested.connect(self.openDownloadTab)
        self.downloads.downloadHistoryRequested.connect(self.openDownloadHistory)
        self.addTab(self.downloads, icon=Icons.FOLDER, closable=False)
        App.DownloadManager.createdSignal.connect(self.downloaderCreated)
        App.DownloadManager.destroyedSignal.connect(self.downloaderDestroyed)
        App.DownloadManager.startedSignal.connect(self.downloadStarted)
        App.DownloadManager.completedSignal.connect(self.downloadCompleted)
        App.DownloadManager.completedSignal.connect(self.performScheduledShutdown, QtCore.Qt.ConnectionType.QueuedConnection)
        App.DownloadManager.runningCountChangedSignal.connect(self._changePageText)
        App.ScheduledDownloadManager.enabledChangedSignal.connect(self.scheduledDownloadEnabledChanged)
        if not Utils.isSystemShutdownSupported():
            self.downloads._ui.scheduledShutdown.removeItem(ScheduledShutdownTypes.SHUTDOWN_SYSTEM.value)
        self.setScheduledShutdown(None)
        self.scheduledDownloadEnabledChanged(App.ScheduledDownloadManager.isEnabled())

    def openDownloadTab(self, downloaderId: uuid.UUID) -> None:
        tabIndex = self.getUniqueTabIndex(downloaderId)
        if tabIndex == None:
            downloadTab = Ui.Download(downloaderId, parent=self)
            downloadTab.accountPageShowRequested.connect(self.accountPageShowRequested)
            tabIndex = self.addTab(downloadTab, icon=Icons.DOWNLOAD, uniqueValue=downloaderId)
        self.setCurrentIndex(tabIndex)
        self.pageObject.show()

    def closeDownloadTab(self, downloaderId: uuid.UUID) -> None:
        tabIndex = self.getUniqueTabIndex(downloaderId)
        if tabIndex != None:
            self.closeTab(tabIndex)

    def openDownloadHistory(self) -> None:
        tabIndex = self.getUniqueTabIndex(Ui.DownloadHistories)
        if tabIndex == None:
            downloadHistoryTab = Ui.DownloadHistories(parent=self)
            downloadHistoryTab.accountPageShowRequested.connect(self.accountPageShowRequested)
            tabIndex = self.addTab(downloadHistoryTab, icon=Icons.HISTORY, uniqueValue=Ui.DownloadHistories)
        self.setCurrentIndex(tabIndex)
        self.pageObject.show()

    def downloaderCreated(self, downloaderId: uuid.UUID) -> None:
        self.downloads.downloaderCreated(downloaderId)
        if App.Preferences.general.isOpenProgressWindowEnabled():
            self.openDownloadTab(downloaderId)
        App.DownloadManager.get(downloaderId).start()

    def downloaderDestroyed(self, downloaderId: uuid.UUID) -> None:
        self.downloads.downloaderDestroyed(downloaderId)
        self.closeDownloadTab(downloaderId)

    def downloadStarted(self, downloaderId: uuid.UUID) -> None:
        self.downloads.downloadStarted(downloaderId)

    def downloadCompleted(self, downloaderId: uuid.UUID) -> None:
        self.downloads.downloadCompleted(downloaderId)

    def _changePageText(self, downloadersCount: int) -> None:
        self.pageObject.setPageName("" if downloadersCount == 0 else str(downloadersCount))

    def setScheduledShutdown(self, action: ScheduledShutdownTypes | None = None) -> None:
        self.downloads._ui.scheduledShutdown.setCurrentIndex((action or ScheduledShutdownTypes.NONE).value)

    def performScheduledShutdown(self) -> None:
        if App.DownloadManager.isDownloaderRunning():
            return
        if self.downloads._ui.scheduledShutdown.currentIndex() == ScheduledShutdownTypes.SHUTDOWN_APP.value:
            if TimedMessageBox(
                T("warning"),
                T("#{appName} will shut down soon.", appName=Config.APP_NAME),
                defaultButton=TimedMessageBox.StandardButton.Cancel,
                autoClickButton=TimedMessageBox.StandardButton.Ok,
                time=Config.APP_SHUTDOWN_TIMEOUT,
                parent=self
            ).exec() == TimedMessageBox.StandardButton.Ok:
                self.appShutdownRequested.emit()
        elif self.downloads._ui.scheduledShutdown.currentIndex() == ScheduledShutdownTypes.SHUTDOWN_SYSTEM.value:
            if TimedMessageBox(
                T("warning"),
                T("#System will shut down soon."),
                defaultButton=TimedMessageBox.StandardButton.Cancel,
                autoClickButton=TimedMessageBox.StandardButton.Ok,
                time=Config.SYSTEM_SHUTDOWN_TIMEOUT,
                parent=self
            ).exec() == TimedMessageBox.StandardButton.Ok:
                self.systemShutdownRequested.emit()

    def scheduledDownloadEnabledChanged(self, enabled: bool) -> None:
        if enabled:
            self.setScheduledShutdown(None)
        self.downloads._ui.restrictedLabel.setVisible(enabled)
        self.downloads._ui.scheduledShutdownArea.setEnabled(not enabled)