from ..BaseEngine import BaseEngine
from ..File.FileDownloader import FileDownloader

from Core import App
from Core.GlobalExceptions import Exceptions
from Services.Logging.Logger import Logger
from Download.DownloadInfo import DownloadInfo
from Download.Downloader.Core.Engine import Modules

from PyQt6 import QtCore


class FileEngine(BaseEngine):
    def __init__(self, downloadInfo: DownloadInfo, status: Modules.Status, progress: Modules.Progress, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(downloadInfo, status, progress, logger, parent=parent)
        self._fileDownloader: FileDownloader | None = None

    def start(self) -> None:
        super().start()
        self._fileDownloader = FileDownloader(
            self._networkAccessManager,
            self.downloadInfo.getUrl(),
            self.downloadInfo.getAbsoluteFileName(),
            priority=self.downloadInfo.getPriority(),
            parent=self
        )
        self._fileDownloader.progressChanged.connect(self._updateProgress)
        self._fileDownloader.errorOccurred.connect(self._fileDownloadFailed)
        self._fileDownloader.finished.connect(self._fileDownloadFinished)
        App.FileDownloadManager.startDownload(self._fileDownloader)

    def _updateProgress(self, bytesReceived: int, bytesTotal: int) -> None:
        self.progress.totalByteSize = bytesReceived
        self.progress.byteSize = bytesTotal
        self._syncProgress()

    def _fileDownloadFailed(self, fileDownloader: FileDownloader) -> None:
        super()._raiseException(fileDownloader.getError())

    def _fileDownloadFinished(self, fileDownloader: FileDownloader) -> None:
        self._finish()

    def _finish(self) -> None:
        self._fileDownloader.setParent(None)
        self._fileDownloader = None
        super()._finish()

    def _raiseException(self, exception: Exceptions.AbortRequested | Exceptions.FileSystemError | Exceptions.NetworkError) -> None:
        super()._raiseException(exception)
        App.FileDownloadManager.cancelDownload(self._fileDownloader)