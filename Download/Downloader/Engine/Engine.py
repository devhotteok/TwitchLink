from Download.Downloader.Engine.Stream.Stream import StreamDownloader
from Download.Downloader.Engine.Video.Video import VideoDownloader
from Download.Downloader.Engine.Clip.Clip import ClipDownloader


class Exceptions:
    class DownloaderCreationDisabled(Exception):
        def __str__(self):
            return "Downloader Creation Disabled"


class TwitchDownloader:
    creationEnabled = False

    @classmethod
    def setCreationEnabled(cls, enabled):
        cls.creationEnabled = enabled

    @classmethod
    def isCreationEnabled(cls):
        return cls.creationEnabled

    @classmethod
    def create(cls, downloadInfo, parent=None):
        if not cls.isCreationEnabled():
            raise Exceptions.DownloaderCreationDisabled
        if downloadInfo.type.isStream():
            downloader = StreamDownloader
        elif downloadInfo.type.isVideo():
            downloader = VideoDownloader
        else:
            downloader = ClipDownloader
        return downloader(downloadInfo, parent=parent)