from Download.DownloadInfo import DownloadInfo
from Download.Downloader.TwitchDownloader import TwitchDownloader
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader

from PyQt6 import QtCore

import uuid


class DownloadManager(QtCore.QObject):
    createdSignal = QtCore.pyqtSignal(object)
    destroyedSignal = QtCore.pyqtSignal(object)
    startedSignal = QtCore.pyqtSignal(object)
    completedSignal = QtCore.pyqtSignal(object)
    runningCountChangedSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.downloaders: dict[uuid.UUID, StreamDownloader | VideoDownloader | ClipDownloader] = {}
        self.runningDownloaders: list[StreamDownloader | VideoDownloader | ClipDownloader] = []

    def onStart(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.runningDownloaders.append(downloader)
        self.runningCountChangedSignal.emit(len(self.runningDownloaders))
        self.startedSignal.emit(downloader.getId())

    def onFinish(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.runningDownloaders.remove(downloader)
        self.runningCountChangedSignal.emit(len(self.runningDownloaders))
        self.completedSignal.emit(downloader.getId())

    def create(self, downloadInfo: DownloadInfo) -> uuid.UUID:
        downloader = TwitchDownloader.create(downloadInfo, parent=self)
        downloader.started.connect(self.onStart)
        downloader.finished.connect(self.onFinish)
        downloaderId = downloader.getId()
        self.downloaders[downloaderId] = downloader
        self.createdSignal.emit(downloaderId)
        return downloaderId

    def get(self, downloaderId: uuid.UUID) -> StreamDownloader | VideoDownloader | ClipDownloader:
        return self.downloaders[downloaderId]

    def remove(self, downloaderId: uuid.UUID) -> None:
        if not self.downloaders[downloaderId].isRunning():
            self.downloaders.pop(downloaderId).deleteLater()
            self.destroyedSignal.emit(downloaderId)

    def cancelAll(self) -> None:
        for downloader in self.downloaders.values():
            downloader.cancel()

    def getRunningDownloaders(self) -> list[StreamDownloader | VideoDownloader | ClipDownloader]:
        return self.runningDownloaders

    def isDownloaderRunning(self) -> bool:
        return len(self.getRunningDownloaders()) != 0