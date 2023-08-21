from Core import App
from Download.DownloadInfo import DownloadInfo
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader

from PyQt6 import QtCore


class Exceptions:
    class DownloaderCreationDisabled(Exception):
        def __str__(self):
            return "Downloader Creation Disabled"


class TwitchDownloader:
    creationEnabled = False

    @classmethod
    def setCreationEnabled(cls, enabled: bool) -> None:
        cls.creationEnabled = enabled

    @classmethod
    def isCreationEnabled(cls) -> bool:
        return cls.creationEnabled

    @classmethod
    def create(cls, downloadInfo: DownloadInfo, parent: QtCore.QObject | None = None) -> StreamDownloader | VideoDownloader | ClipDownloader:
        if not cls.isCreationEnabled():
            raise Exceptions.DownloaderCreationDisabled
        App.ContentManager.checkRestriction(downloadInfo.content)
        if downloadInfo.type.isStream():
            downloader = StreamDownloader(downloadInfo, parent=parent)
        elif downloadInfo.type.isVideo():
            downloader = VideoDownloader(downloadInfo, parent=parent)
        else:
            downloader = ClipDownloader(downloadInfo, parent=parent)
        App.Instance.logger.info(f"Created downloader with logger '{downloader.logger.getPath()}'.")
        return downloader