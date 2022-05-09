from Core.Ui import *
from Download.DownloadManager import DownloadManager
from Ui.Operators.TabManager import TabManager
from Ui.Operators.TimedMessageBox import TimedMessageBox
from Ui.Operators.TimedCancelDialog import TimedCancelDialog


class DownloadCompleteAction:
    NONE = 0
    SHUTDOWN_APP = 1
    SHUTDOWN_SYSTEM = 2


class DownloadsPage(TabManager):
    appShutdownRequested = QtCore.pyqtSignal()
    systemShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, pageObject, parent=None):
        super(DownloadsPage, self).__init__(parent=parent)
        self.pageObject = pageObject
        self.downloads = Ui.Downloads(parent=self)
        self.downloads.progressWindowRequested.connect(self.openDownloadTab)
        self.addTab(self.downloads, icon=Icons.FOLDER_ICON, closable=False)
        DownloadManager.createdSignal.connect(self.downloaderCreated)
        DownloadManager.destroyedSignal.connect(self.downloaderDestroyed)
        DownloadManager.completedSignal.connect(self.downloadCompleted)
        DownloadManager.runningCountChangedSignal.connect(self.changePageText)

    def openDownloadTab(self, downloaderId):
        tabIndex = self.getUniqueTabIndex(downloaderId)
        if tabIndex == None:
            tabIndex = self.addTab(Ui.Download(downloaderId, parent=self), icon=Icons.DOWNLOAD_ICON, uniqueValue=downloaderId)
        self.setCurrentIndex(tabIndex)
        self.pageObject.show()

    def closeDownloadTab(self, downloaderId):
        tabIndex = self.getUniqueTabIndex(downloaderId)
        if tabIndex != None:
            self.closeTab(tabIndex)

    def downloaderCreated(self, downloaderId):
        self.downloads.downloaderCreated(downloaderId)
        if DB.general.isOpenProgressWindowEnabled():
            self.openDownloadTab(downloaderId)

    def downloaderDestroyed(self, downloaderId):
        self.downloads.downloaderDestroyed(downloaderId)
        self.closeDownloadTab(downloaderId)

    def downloadCompleted(self, downloaderId):
        self.downloads.downloadCompleted(downloaderId)
        if not DownloadManager.isDownloaderRunning():
            self.performDownloadCompleteAction()

    def changePageText(self, downloadersCount):
        self.pageObject.setPageName("" if downloadersCount == 0 else str(downloadersCount))

    def performDownloadCompleteAction(self):
        if self.downloads.downloadCompleteAction.currentIndex() == DownloadCompleteAction.SHUTDOWN_APP:
            if TimedMessageBox(
                T("warning"),
                T("#{appName} will shut down soon.", appName=Config.APP_NAME),
                defaultButton=TimedMessageBox.StandardButton.Cancel,
                autoClickButton=TimedMessageBox.StandardButton.Ok,
                time=Config.APP_SHUTDOWN_TIMEOUT,
                parent=self
            ).exec() == TimedMessageBox.StandardButton.Ok:
                self.appShutdownRequested.emit()
        elif self.downloads.downloadCompleteAction.currentIndex() == DownloadCompleteAction.SHUTDOWN_SYSTEM:
            dialog = TimedCancelDialog(
                T("warning"),
                T("#The system will shut down after {seconds} seconds.", autoFormat=False),
                time=Config.SYSTEM_SHUTDOWN_TIMEOUT,
                parent=self
            )
            dialog.setMinimumSize(self.size() / 2)
            dialog.exec()
            if not dialog.wasCanceled():
                self.systemShutdownRequested.emit()