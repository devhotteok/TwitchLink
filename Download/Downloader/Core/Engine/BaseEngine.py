from Core.Config import Config
from Core.GlobalExceptions import Exceptions
from Services.Logging.Logger import Logger
from Download.DownloadInfo import DownloadInfo
from Download.Downloader.Core.Engine import Modules

from PyQt6 import QtCore, QtNetwork


class BaseEngine(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, downloadInfo: DownloadInfo, status: Modules.Status, progress: Modules.Progress, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.downloadInfo = downloadInfo
        self.status = status
        self.progress = progress
        self.logger = logger
        self._networkAccessManager = QtNetwork.QNetworkAccessManager(parent=self)
        self.file = QtCore.QFile(self.downloadInfo.getAbsoluteFileName(), self)
        self.file.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)

    def start(self) -> None:
        self.status.setDownloading()
        self._syncStatus()
        self.logger.debug(f"{Config.APP_NAME} {Config.APP_VERSION}\n\n[Download Info]\n{Logger.generateObjectLog(self.downloadInfo)}")
        self.logger.info("Download Started")

    def _finish(self) -> None:
        self.file.close()
        if self._isFileRemoveRequired():
            self.file.remove()
            self.status.setFileRemoved()
        if self.status.terminateState.isProcessing():
            self.status.terminateState.setTrue()
            if isinstance(self.status.getError(), Exceptions.AbortRequested):
                self.logger.info("Download Abort Requested")
            else:
                self.logger.info("Download Failed")
                self.logger.warning("Download failed for the following reason.")
                self.logger.exception(self.status.getError())
        else:
            self.logger.info("Download Completed")
        self.status.setDone()
        self._syncStatus()
        self.finished.emit()

    def abort(self, exception: Exception) -> None:
        self.logger.warning("Abort requested with the following exception.")
        self.logger.warning(exception)
        self._raiseException(exception)

    def _raiseException(self, exception: Exception) -> None:
        self.status.raiseError(exception)
        self._syncStatus()

    def _isFileRemoveRequired(self) -> bool:
        return self.file.size() == 0

    def _syncStatus(self) -> None:
        self.status.sync()
        self.progress.sync()

    def _syncProgress(self) -> None:
        self.progress.sync()