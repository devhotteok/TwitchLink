from Download.Downloader.Engine.Stream.Stream import StreamDownloader
from Download.Downloader.Engine.Video.Video import VideoDownloader
from Download.Downloader.Engine.Clip.Clip import ClipDownloader


def TwitchDownloader(downloadInfo, parent=None):
    if downloadInfo.type.isStream():
        downloader = StreamDownloader
    elif downloadInfo.type.isVideo():
        downloader = VideoDownloader
    else:
        downloader = ClipDownloader
    return downloader(downloadInfo, parent=parent)