from Core.App import App
from Services.Messages import Messages
from Services.Utils.Utils import Utils
from Services.Translator.Translator import T
from Database.Database import DB
from Download.Downloader.Engine.Engine import TwitchDownloader
from Download.DownloadManager import DownloadManager
from Download.ScheduledDownloadManager import ScheduledDownloadManager
from Download.DownloadHistoryManager import DownloadHistoryManager

from PyQt6 import QtCore


class _GlobalDownloadManager(QtCore.QObject):
    runningCountChangedSignal = QtCore.pyqtSignal(int)
    statsUpdated = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(_GlobalDownloadManager, self).__init__(parent=parent)
        DownloadManager.createdSignal.connect(self._downloadManagerDownloaderCreated)
        DownloadManager.startedSignal.connect(self._downloadManagerDownloadStarted)
        DownloadManager.completedSignal.connect(self._downloadManagerDownloadFinished)
        ScheduledDownloadManager.downloaderCreatedSignal.connect(self._scheduledDownloaderCreated)
        ScheduledDownloadManager.downloaderDestroyedSignal.connect(self._scheduledDownloaderDestroyed)
        self._representativeDownloader = None

    def setDownloaderCreationEnabled(self, enabled):
        TwitchDownloader.setCreationEnabled(enabled)

    def _downloadManagerDownloaderCreated(self, downloaderId):
        DownloadHistoryManager.createHistory(DownloadManager.get(downloaderId))

    def _scheduledDownloaderCreated(self, scheduledDownload, downloader):
        DownloadHistoryManager.createHistory(downloader)
        self.downloadStarted(downloader)
        if DB.general.isNotifyEnabled():
            App.notification.toastMessage(
                title=T("download-started"),
                message=f"{T('title')}: {downloader.setup.downloadInfo.videoData.title}\n{T('file')}: {downloader.setup.downloadInfo.getAbsoluteFileName()}"
            )

    def _scheduledDownloaderDestroyed(self, scheduledDownload, downloader):
        self.downloadFinished(downloader)
        if DB.general.isNotifyEnabled():
            if downloader.status.terminateState.isTrue():
                if downloader.status.getError() == None:
                    title = "download-stopped"
                else:
                    title = "download-aborted"
            else:
                title = "download-complete"
            App.notification.toastMessage(
                title=T(title),
                message=f"{T('title')}: {downloader.setup.downloadInfo.videoData.title}\n{T('file')}: {downloader.setup.downloadInfo.getAbsoluteFileName()}",
                actions={
                    T("open-file"): lambda: _GlobalDownloadManager.openFile(downloader.setup.downloadInfo.getAbsoluteFileName()),
                    T("open-folder"): lambda: _GlobalDownloadManager.openFolder(downloader.setup.downloadInfo.directory)
                } if downloader.status.getError() == None else None
            )

    def _downloadManagerDownloadStarted(self, downloaderId):
        self.downloadStarted(DownloadManager.get(downloaderId))

    def _downloadManagerDownloadFinished(self, downloaderId):
        self.downloadFinished(DownloadManager.get(downloaderId))

    def downloadStarted(self, downloader):
        representativeDownloader = self.getRepresentativeDownloader()
        if representativeDownloader == None:
            if self._representativeDownloader != None:
                self.hideDownloaderProgress(complete=False)
        else:
            self.showDownloaderProgress(representativeDownloader)
        self.runningCountChangedSignal.emit(len(self.getRunningDownloaders()))

    def downloadFinished(self, downloader):
        representativeDownloader = self.getRepresentativeDownloader()
        if representativeDownloader == None:
            if self._representativeDownloader != None:
                self.hideDownloaderProgress(complete=True)
        else:
            self.showDownloaderProgress(representativeDownloader)
        self.updateDownloadStats(downloader)
        self.runningCountChangedSignal.emit(len(self.getRunningDownloaders()))

    def updateDownloadStats(self, downloader):
        if downloader.status.terminateState.isTrue():
            if downloader.status.getError() == None:
                if not downloader.setup.downloadInfo.type.isStream():
                    return
            else:
                return
        DB.temp.updateDownloadStats(downloader.progress.totalByteSize)
        self.statsUpdated.emit(DB.temp.getDownloadStats())

    def getRepresentativeDownloader(self):
        runningDownloaders = self.getRunningDownloaders()
        if len(self.getRunningDownloaders()) == 1:
            return runningDownloaders[0]
        else:
            return None

    def showDownloaderProgress(self, downloader):
        self._representativeDownloader = downloader
        self._representativeDownloader.hasUpdate.connect(self.handleRepresentativeDownloader)
        App.taskbar.show(indeterminate=self._representativeDownloader.setup.downloadInfo.type.isStream())
        self._representativeDownloader.hasUpdate.emit()

    def hideDownloaderProgress(self, complete):
        self._representativeDownloader.hasUpdate.disconnect(self.handleRepresentativeDownloader)
        self._representativeDownloader = None
        if complete:
            App.taskbar.complete()
        else:
            App.taskbar.hide()

    def cancelAll(self):
        DownloadManager.cancelAll()
        ScheduledDownloadManager.cancelAll()

    def waitAll(self):
        DownloadManager.waitAll()
        ScheduledDownloadManager.waitAll()

    def getAllDownloaders(self):
        return [*DownloadManager.downloaders, *ScheduledDownloadManager.getRunningDownloaders()]

    def getRunningDownloaders(self):
        return [*DownloadManager.getRunningDownloaders(), *ScheduledDownloadManager.getRunningDownloaders()]

    def isDownloaderRunning(self):
        return len(self.getRunningDownloaders()) != 0

    def isShuttingDown(self):
        return not any(downloader.status.terminateState.isFalse() for downloader in self.getRunningDownloaders())

    def handleRepresentativeDownloader(self):
        if self._representativeDownloader.setup.downloadInfo.type.isStream():
            self.handleStreamProgress(self._representativeDownloader)
        elif self._representativeDownloader.setup.downloadInfo.type.isVideo():
            self.handleVideoProgress(self._representativeDownloader)
        else:
            self.handleClipProgress(self._representativeDownloader)

    def handleStreamProgress(self, downloader):
        status = downloader.status
        if not status.terminateState.isFalse():
            App.taskbar.stop()

    def handleVideoProgress(self, downloader):
        status = downloader.status
        progress = downloader.progress
        if status.isEncoding():
            App.taskbar.setValue(progress.timeProgress)
        else:
            App.taskbar.setValue(progress.fileProgress)
        if not status.terminateState.isFalse():
            App.taskbar.stop()
        elif not status.pauseState.isFalse() or status.isWaiting() or status.isUpdating() or status.isEncoding():
            App.taskbar.pause()

    def handleClipProgress(self, downloader):
        progress = downloader.progress
        App.taskbar.setValue(progress.sizeProgress)

    @staticmethod
    def openFile(fileName):
        try:
            Utils.openFile(fileName)
        except:
            Utils.info(*Messages.INFO.FILE_NOT_FOUND)

    @staticmethod
    def openFolder(directory):
        try:
            Utils.openFile(directory)
        except:
            Utils.info(*Messages.INFO.FOLDER_NOT_FOUND)

GlobalDownloadManager = _GlobalDownloadManager()