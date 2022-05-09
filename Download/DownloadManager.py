from Core.App import App
from Download.Downloader.Engine.Engine import TwitchDownloader

from PyQt5 import QtCore


class _DownloadManager(QtCore.QObject):
    createdSignal = QtCore.pyqtSignal(object)
    destroyedSignal = QtCore.pyqtSignal(object)
    completedSignal = QtCore.pyqtSignal(object)
    runningCountChangedSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(_DownloadManager, self).__init__(parent=parent)
        self.downloaders = {}
        self.runningDownloaders = []
        self.singleDownloader = None

    def onStart(self, downloader):
        if len(self.runningDownloaders) == 0:
            self.showDownloaderProgress(downloader)
        elif len(self.runningDownloaders) == 1:
            self.hideDownloaderProgress(complete=False)
        self.runningDownloaders.append(downloader)
        self.runningCountChangedSignal.emit(len(self.runningDownloaders))

    def onFinish(self, downloader):
        self.runningDownloaders.remove(downloader)
        if len(self.runningDownloaders) == 0:
            self.hideDownloaderProgress(complete=True)
        elif len(self.runningDownloaders) == 1:
            self.showDownloaderProgress(self.runningDownloaders[0])
        self.completedSignal.emit(downloader.getId())
        self.runningCountChangedSignal.emit(len(self.runningDownloaders))

    def showDownloaderProgress(self, downloader):
        self.singleDownloader = downloader
        self.singleDownloader.hasUpdate.connect(self.handleSingleDownloader)
        App.taskbar.show(indeterminate=self.singleDownloader.setup.downloadInfo.type.isStream())
        self.singleDownloader.hasUpdate.emit()

    def hideDownloaderProgress(self, complete):
        self.singleDownloader.hasUpdate.disconnect(self.handleSingleDownloader)
        self.singleDownloader = None
        if complete:
            App.taskbar.complete()
        else:
            App.taskbar.hide()

    def create(self, downloadInfo):
        downloader = TwitchDownloader(downloadInfo, parent=self)
        downloader.needSetup.connect(self.onStart)
        downloader.needCleanup.connect(self.onFinish)
        downloaderId = downloader.getId()
        self.downloaders[downloaderId] = downloader
        self.createdSignal.emit(downloaderId)
        return downloaderId

    def get(self, downloaderId):
        return self.downloaders[downloaderId]

    def cancelAll(self):
        for downloader in self.downloaders.values():
            downloader.cancel()

    def waitAll(self):
        for downloader in self.downloaders.values():
            downloader.wait()

    def remove(self, downloaderId):
        self.downloaders[downloaderId].cancel()
        self.downloaders[downloaderId].wait()
        self.downloaders.pop(downloaderId).setParent(None)
        self.destroyedSignal.emit(downloaderId)

    def getRunningDownloaders(self):
        return self.runningDownloaders

    def isDownloaderRunning(self):
        return len(self.getRunningDownloaders()) != 0

    def isShuttingDown(self):
        for downloader in self.runningDownloaders:
            if not downloader.setup.downloadInfo.type.isClip() and downloader.status.terminateState.isFalse():
                return False
        return True

    def handleSingleDownloader(self):
        if self.singleDownloader.setup.downloadInfo.type.isStream():
            self.handleStreamProgress(self.singleDownloader)
        elif self.singleDownloader.setup.downloadInfo.type.isVideo():
            self.handleVideoProgress(self.singleDownloader)
        else:
            self.handleClipProgress(self.singleDownloader)

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
        elif not status.pauseState.isFalse() or status.isWaiting() or status.isEncoding():
            App.taskbar.pause()

    def handleClipProgress(self, downloader):
        progress = downloader.progress
        App.taskbar.setValue(progress.byteSizeProgress)


DownloadManager = _DownloadManager()