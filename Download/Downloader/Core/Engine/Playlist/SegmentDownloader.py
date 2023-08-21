from ..File import FileDownloadManager

from Services.Playlist.Segment import Segment

from PyQt6 import QtCore, QtNetwork


class SegmentDownloader(FileDownloadManager.FileDownloader):
    def __init__(self, networkAccessManager: QtNetwork.QNetworkAccessManager, segment: Segment, filePath: str, priority: int = 0, parent: QtCore.QObject | None = None):
        super().__init__(networkAccessManager, segment.url, filePath, priority=priority, parent=parent)
        self.segment = segment