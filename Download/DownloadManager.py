from Services.FileNameManager import FileNameManager
from Download.Downloader.Engine.Engine import TwitchDownloader

from PyQt5 import QtCore


class _DownloadManager(QtCore.QObject):
    createdSignal = QtCore.pyqtSignal(object)
    destroyedSignal = QtCore.pyqtSignal(object)
    startedSignal = QtCore.pyqtSignal(object)
    completedSignal = QtCore.pyqtSignal(object)
    runningCountChangedSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(_DownloadManager, self).__init__(parent=parent)
        self.downloaders = {}
        self.runningDownloaders = []

    def onStart(self, downloader):
        self.runningDownloaders.append(downloader)
        self.runningCountChangedSignal.emit(len(self.runningDownloaders))
        self.startedSignal.emit(downloader.getId())

    def onFinish(self, downloader):
        self.runningDownloaders.remove(downloader)
        self.runningCountChangedSignal.emit(len(self.runningDownloaders))
        FileNameManager.unlock(downloader.setup.downloadInfo.getAbsoluteFileName())
        self.completedSignal.emit(downloader.getId())

    def create(self, downloadInfo):
        FileNameManager.lock(downloadInfo.getAbsoluteFileName())
        downloader = TwitchDownloader.create(downloadInfo, parent=self)
        downloader.started.connect(self.onStart)
        downloader.finished.connect(self.onFinish)
        downloaderId = downloader.getId()
        self.downloaders[downloaderId] = downloader
        self.createdSignal.emit(downloaderId)
        return downloaderId

    def get(self, downloaderId):
        return self.downloaders[downloaderId]

    def remove(self, downloaderId):
        self.downloaders[downloaderId].cancel()
        self.downloaders[downloaderId].wait()
        self.downloaders.pop(downloaderId).setParent(None)
        self.destroyedSignal.emit(downloaderId)

    def cancelAll(self):
        for downloader in self.downloaders.values():
            downloader.cancel()

    def waitAll(self):
        for downloader in self.downloaders.values():
            downloader.wait()

    def getRunningDownloaders(self):
        return self.runningDownloaders

    def isDownloaderRunning(self):
        return len(self.getRunningDownloaders()) != 0

DownloadManager = _DownloadManager()