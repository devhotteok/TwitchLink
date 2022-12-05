from Core.GlobalExceptions import Exceptions
from Services import ContentManager
from Database.Database import DB
from Database.EncoderDecoder import Codable
from Download.DownloadManager import DownloadManager

from PyQt5 import QtCore


class DownloadHistory(QtCore.QObject, Codable):
    CODABLE_INIT_MODEL = False
    CODABLE_STRICT_MODE = False
    CODABLE_REQUIRED_DATA = ["downloadInfo", "startedAt", "completedAt", "logFile", "result"]

    historyChanged = QtCore.pyqtSignal()

    class Result:
        downloading = "downloading"
        completed = "download-complete"
        skipped = "download-skipped"
        stopped = "download-stopped"
        canceled = "download-canceled"
        aborted = "download-aborted"

    def __init__(self, downloaderId, parent=None):
        super(DownloadHistory, self).__init__(parent=parent)
        downloader = DownloadManager.get(downloaderId)
        self.downloadInfo = downloader.setup.downloadInfo
        self.startedAt = QtCore.QDateTime.currentDateTimeUtc()
        self.completedAt = None
        self.logFile = downloader.logger.getPath()
        self.result = self.Result.downloading
        self.error = None
        downloader.finished.connect(self.handleDownloadResult)

    def __setup__(self):
        super(DownloadHistory, self).__init__(parent=None)
        if self.result == self.Result.downloading:
            self.result = self.Result.aborted
            self.error = "unknown-error"

    def handleDownloadResult(self, downloader):
        self.completedAt = QtCore.QDateTime.currentDateTimeUtc()
        if downloader.status.terminateState.isTrue():
            if downloader.status.getError() == None:
                if self.downloadInfo.type.isStream():
                    self.result = self.Result.stopped
                else:
                    self.result = self.Result.canceled
            else:
                self.result = self.Result.aborted
                exception = downloader.status.getError()
                if isinstance(exception, Exceptions.FileSystemError):
                    self.error = "system-error"
                elif isinstance(exception, Exceptions.NetworkError):
                    self.error = "network-error"
                elif isinstance(exception, ContentManager.Exceptions.RestrictedContent):
                    self.error = "restricted-content"
                else:
                    self.error = "unknown-error"
        else:
            self.result = self.Result.skipped if downloader.status.isDownloadSkipped() else self.Result.completed
        self.historyChanged.emit()


class _DownloadHistoryManager(QtCore.QObject):
    historyCreated = QtCore.pyqtSignal(DownloadHistory)
    historyRemoved = QtCore.pyqtSignal(DownloadHistory)

    def __init__(self, parent=None):
        super(_DownloadHistoryManager, self).__init__(parent=parent)
        DownloadManager.createdSignal.connect(self.downloaderCreated)

    def getHistoryList(self):
        return DB.temp.getDownloadHistory()

    def downloaderCreated(self, downloaderId):
        downloadHistory = DownloadHistory(downloaderId)
        DB.temp.addDownloadHistory(downloadHistory)
        self.historyCreated.emit(downloadHistory)

    def removeHistory(self, downloadHistory):
        DB.temp.removeDownloadHistory(downloadHistory)
        self.historyRemoved.emit(downloadHistory)

DownloadHistoryManager = _DownloadHistoryManager()