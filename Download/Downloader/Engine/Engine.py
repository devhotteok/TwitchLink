from .Stream import StreamDownloader
from .Video import VideoDownloader
from .Clip import ClipDownloader


def TwitchDownloader(downloadInfo, **kwargs):
    if downloadInfo.type.isStream():
        downloader = StreamDownloader
    elif downloadInfo.type.isVideo():
        downloader = VideoDownloader
    else:
        downloader = ClipDownloader
    return downloader(downloadInfo, **kwargs)