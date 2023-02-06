from Core.Ui import *
from Download.DownloadManager import DownloadManager
from Download.ScheduledDownloadManager import ScheduledDownloadManager
from Ui.Components.Operators.TabManager import TabManager
from Ui.Components.Widgets.TimedMessageBox import TimedMessageBox
from Ui.Components.Widgets.TimedCancelDialog import TimedCancelDialog


class DownloadCompleteAction:
    NONE = 0
    SHUTDOWN_APP = 1
    SHUTDOWN_SYSTEM = 2


class DownloadsPage(TabManager):
    accountPageShowRequested = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()
    systemShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, pageObject, parent=None):
        super(DownloadsPage, self).__init__(parent=parent)
        self.pageObject = pageObject
        self.downloads = Ui.Downloads(parent=self)
        self.downloads.progressWindowRequested.connect(self.openDownloadTab)
        self.downloads.downloadHistoryRequested.connect(self.openDownloadHistory)
        self.addTab(self.downloads, icon=Icons.FOLDER_ICON, closable=False)
        DownloadManager.createdSignal.connect(self.downloaderCreated)
        DownloadManager.destroyedSignal.connect(self.downloaderDestroyed)
        DownloadManager.startedSignal.connect(self.downloadStarted)
        DownloadManager.completedSignal.connect(self.downloadCompleted)
        DownloadManager.completedSignal.connect(self.processCompleteEvent, QtCore.Qt.QueuedConnection)
        DownloadManager.completedSignal.connect(self.performDownloadCompleteAction, QtCore.Qt.QueuedConnection)
        DownloadManager.runningCountChangedSignal.connect(self.changePageText)
        ScheduledDownloadManager.enabledChangedSignal.connect(self.scheduledDownloadEnabledChanged)
        self.scheduledDownloadEnabledChanged(ScheduledDownloadManager.isEnabled())

    def openDownloadTab(self, downloaderId):
        tabIndex = self.getUniqueTabIndex(downloaderId)
        self.setCurrentIndex(self.addTab(Ui.Download(downloaderId, parent=self), icon=Icons.DOWNLOAD_ICON, uniqueValue=downloaderId) if tabIndex == None else tabIndex)
        self.pageObject.show()

    def closeDownloadTab(self, downloaderId):
        tabIndex = self.getUniqueTabIndex(downloaderId)
        if tabIndex != None:
            self.closeTab(tabIndex)

    def openDownloadHistory(self):
        tabIndex = self.getUniqueTabIndex(Ui.DownloadHistory)
        if tabIndex == None:
            downloadHistoryTab = Ui.DownloadHistory(parent=self)
            downloadHistoryTab.accountPageShowRequested.connect(self.accountPageShowRequested)
            tabIndex = self.addTab(downloadHistoryTab, icon=Icons.HISTORY_ICON, uniqueValue=Ui.DownloadHistory)
        self.setCurrentIndex(tabIndex)
        self.pageObject.show()

    def downloaderCreated(self, downloaderId):
        self.downloads.downloaderCreated(downloaderId)
        if DB.general.isOpenProgressWindowEnabled():
            self.openDownloadTab(downloaderId)
        DownloadManager.get(downloaderId).start()

    def downloaderDestroyed(self, downloaderId):
        self.downloads.downloaderDestroyed(downloaderId)
        self.closeDownloadTab(downloaderId)

    def downloadStarted(self, downloaderId):
        self.downloads.downloadStarted(downloaderId)

    def downloadCompleted(self, downloaderId):
        self.downloads.downloadCompleted(downloaderId)

    def processCompleteEvent(self, downloaderId):
        self.downloads.processCompleteEvent(downloaderId)

    def changePageText(self, downloadersCount):
        self.pageObject.setPageName("" if downloadersCount == 0 else str(downloadersCount))

    def setDownloadCompleteAction(self, action=None):
        self.downloads.downloadCompleteAction.setCurrentIndex(action or DownloadCompleteAction.NONE)

    def getDownloadCompleteAction(self):
        return self.downloads.downloadCompleteAction.currentIndex()

    def performDownloadCompleteAction(self):
        if DownloadManager.isDownloaderRunning():
            return
        if self.getDownloadCompleteAction() == DownloadCompleteAction.SHUTDOWN_APP:
            if TimedMessageBox(
                T("warning"),
                T("#{appName} will shut down soon.", appName=Config.APP_NAME),
                defaultButton=TimedMessageBox.StandardButton.Cancel,
                autoClickButton=TimedMessageBox.StandardButton.Ok,
                time=Config.APP_SHUTDOWN_TIMEOUT,
                parent=self
            ).exec() == TimedMessageBox.StandardButton.Ok:
                self.appShutdownRequested.emit()
        elif self.getDownloadCompleteAction() == DownloadCompleteAction.SHUTDOWN_SYSTEM:
            dialog = TimedCancelDialog(
                T("warning"),
                T("#The system will shut down after {seconds} seconds."),
                time=Config.SYSTEM_SHUTDOWN_TIMEOUT,
                parent=self
            )
            dialog.exec()
            if not dialog.wasCanceled():
                self.systemShutdownRequested.emit()

    def scheduledDownloadEnabledChanged(self, enabled):
        if enabled:
            self.setDownloadCompleteAction(None)
        self.downloads.restrictedLabel.setVisible(enabled)
        self.downloads.downloadCompleteActionArea.setEnabled(not enabled)