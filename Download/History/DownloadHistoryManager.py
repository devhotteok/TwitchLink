from .DownloadHistory import DownloadHistory

from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader

from PyQt6 import QtCore


class DownloadHistoryManager(QtCore.QObject):
    historyCreated = QtCore.pyqtSignal(DownloadHistory)
    historyRemoved = QtCore.pyqtSignal(DownloadHistory)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.downloadHistory = []

    def setHistoryList(self, historyList: DownloadHistory) -> None:
        self.downloadHistory = historyList

    def getHistoryList(self) -> list[DownloadHistory]:
        return self.downloadHistory

    def createHistory(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        downloadHistory = DownloadHistory(downloader, parent=None)
        self.downloadHistory.append(downloadHistory)
        self.historyCreated.emit(downloadHistory)

    def removeHistory(self, downloadHistory: DownloadHistory) -> None:
        self.downloadHistory.remove(downloadHistory)
        self.historyRemoved.emit(downloadHistory)