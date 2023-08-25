from .FileDownloader import FileDownloader

from Services.PriorityQueue import PriorityQueue

from PyQt6 import QtCore

import typing


class FileDownloadManager(QtCore.QObject):
    _startRequested = QtCore.pyqtSignal(object)
    _cancelRequested = QtCore.pyqtSignal(object)

    def __init__(self, poolSize: int = 20, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._poolSize = poolSize
        self._queue = PriorityQueue()
        self._pool = []
        self._tempPool = []
        self._startRequested.connect(self._startDownloadHandler)
        self._cancelRequested.connect(self._cancelDownloadHandler)

    def startDownload(self, fileDownloader: FileDownloader) -> None:
        self._startRequested.emit([fileDownloader])

    def startDownloads(self, fileDownloaders: typing.Iterable[FileDownloader]) -> None:
        self._startRequested.emit([fileDownloader for fileDownloader in fileDownloaders])

    def _startDownloadHandler(self, fileDownloaders: typing.Iterable[FileDownloader]) -> None:
        for fileDownloader in fileDownloaders:
            self._queue.push(fileDownloader, priority=fileDownloader.getPriority())
        self._updateState()

    def cancelDownload(self, fileDownloader: FileDownloader) -> None:
        self._cancelRequested.emit([fileDownloader])

    def cancelDownloads(self, fileDownloaders: typing.Iterable[FileDownloader]) -> None:
        self._cancelRequested.emit([fileDownloader for fileDownloader in fileDownloaders])

    def _cancelDownloadHandler(self, fileDownloaders: typing.Iterable[FileDownloader]) -> None:
        self._queue.removeItems([fileDownloader for fileDownloader in fileDownloaders if fileDownloader in self._queue])
        for fileDownloader in fileDownloaders:
            fileDownloader.abort()

    def setPoolSize(self, poolSize: int) -> None:
        self._poolSize = poolSize
        self._updateState()

    def getPoolSize(self) -> int:
        return self._poolSize

    def _updateState(self) -> None:
        while len(self._pool) < self._poolSize and len(self._queue) != 0:
            downloader = self._queue.pop()
            downloader.finished.connect(self._removeFromPool)
            downloader._retryRequired.connect(self._downloadRetryRequired)
            downloader._retryRequested.connect(self._downloadRetryRequested)
            downloader.start()
            self._pool.append(downloader)

    def _removeFromPool(self, downloader: FileDownloader) -> None:
        downloader.finished.disconnect(self._removeFromPool)
        downloader._retryRequired.disconnect(self._downloadRetryRequired)
        downloader._retryRequested.disconnect(self._downloadRetryRequested)
        self._pool.remove(downloader)
        self._updateState()

    def _downloadRetryRequired(self, downloader: FileDownloader) -> None:
        downloader.finished.disconnect(self._removeFromPool)
        self._pool.remove(downloader)
        self._updateState()
        self._tempPool.append(downloader)
        downloader.finished.connect(self._removeFromTempPool)

    def _removeFromTempPool(self, downloader: FileDownloader) -> None:
        downloader.finished.disconnect(self._removeFromTempPool)
        downloader._retryRequired.disconnect(self._downloadRetryRequired)
        downloader._retryRequested.disconnect(self._downloadRetryRequested)
        self._tempPool.remove(downloader)

    def _downloadRetryRequested(self, downloader: FileDownloader) -> None:
        self._removeFromTempPool(downloader)
        self._queue.push(downloader, priority=downloader.getPriority())
        self._updateState()