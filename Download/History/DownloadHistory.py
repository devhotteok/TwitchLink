from Core.GlobalExceptions import Exceptions
from Services import ContentManager
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader
from Download.Downloader.Core.Engine.Modules import Progress
from AppData.EncoderDecoder import Serializable

from PyQt6 import QtCore


class ProgressDetails(Serializable):
    def __init__(self):
        self.files = 0
        self.totalFiles = 0
        self.mutedFiles = 0
        self.skippedFiles = 0
        self.missingFiles = 0
        self.milliseconds = 0
        self.totalMilliseconds = 0
        self.mutedMilliseconds = 0
        self.skippedMilliseconds = 0
        self.missingMilliseconds = 0
        self.byteSize = 0
        self.totalByteSize = 0

    def update(self, progress: Progress) -> None:
        self.files = progress.files
        self.totalFiles = progress.totalFiles
        self.mutedFiles = progress.mutedFiles
        self.skippedFiles = progress.skippedFiles
        self.missingFiles = progress.missingFiles
        self.milliseconds = progress.milliseconds
        self.totalMilliseconds = progress.totalMilliseconds
        self.mutedMilliseconds = progress.mutedMilliseconds
        self.skippedMilliseconds = progress.skippedMilliseconds
        self.missingMilliseconds = progress.missingMilliseconds
        self.byteSize = progress.byteSize
        self.totalByteSize = progress.totalByteSize


class DownloadHistory(QtCore.QObject, Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    historyUpdated = QtCore.pyqtSignal()

    class Result:
        downloading = "downloading"
        completed = "download-complete"
        stopped = "download-stopped"
        canceled = "download-canceled"
        aborted = "download-aborted"

    def __init__(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._downloader = downloader
        self.downloadInfo = self._downloader.downloadInfo
        self.startedAt = QtCore.QDateTime.currentDateTimeUtc()
        self.completedAt = None
        self.logFile = self._downloader.logger.getPath()
        self.progressDetails = ProgressDetails()
        self.result = self.Result.downloading
        self.error = None
        self._downloader.progress.updated.connect(self._updatProgressDetails)
        self._downloader.finished.connect(self._handleDownloadResult)

    def __update__(self, data):
        self.downloadInfo = data["downloadInfo"]
        self.startedAt = data["startedAt"]
        self.completedAt = data["completedAt"]
        self.logFile = data["logFile"]
        self.progressDetails = data["progressDetails"]
        self.result = data["result"]
        self.error = data["error"]

    def __setup__(self):
        super().__init__(parent=None)
        if self.result == self.Result.downloading:
            self.result = self.Result.aborted
            self.error = "unexpected-error"

    def __save__(self):
        return {
            "downloadInfo": self.downloadInfo,
            "startedAt": self.startedAt,
            "completedAt": self.completedAt,
            "logFile": self.logFile,
            "progressDetails": self.progressDetails,
            "result": self.result,
            "error": self.error
        }

    def _updatProgressDetails(self) -> None:
        self.progressDetails.update(self._downloader.progress)
        self.historyUpdated.emit()

    def _handleDownloadResult(self) -> None:
        self.completedAt = QtCore.QDateTime.currentDateTimeUtc()
        if self._downloader.status.terminateState.isTrue():
            if isinstance(self._downloader.status.getError(), Exceptions.AbortRequested):
                if self.downloadInfo.type.isStream():
                    self.result = self.Result.stopped
                else:
                    self.result = self.Result.canceled
            else:
                self.result = self.Result.aborted
                exception = self._downloader.status.getError()
                if isinstance(exception, Exceptions.FileSystemError):
                    self.error = "system-error"
                elif isinstance(exception, Exceptions.NetworkError):
                    self.error = "network-error"
                elif isinstance(exception, ContentManager.Exceptions.RestrictedContent):
                    self.error = "restricted-content"
                else:
                    self.error = "unexpected-error"
        else:
            self.result = self.Result.completed
        self._downloader.progress.updated.disconnect(self._updatProgressDetails)
        self._downloader.finished.disconnect(self._handleDownloadResult)
        self._downloader = None
        self.historyUpdated.emit()