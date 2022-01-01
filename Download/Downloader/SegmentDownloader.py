from Core.GlobalExceptions import Exceptions
from Services.NetworkRequests import requests
from Services.Utils.Utils import Utils
from Download.Downloader.Engine.Config import Config
from Download.Downloader.Task.PrioritizedTask import PrioritizedTask


class SegmentDownloader(PrioritizedTask):
    def __init__(self, url, segment, unmute, saveAs, priority=0):
        super().__init__(target=self.download, priority=priority)
        self.urls = self.getFileUrls(url, segment, unmute)
        self.saveAs = saveAs

    def download(self):
        for i in range(Config.SEGMENT_DOWNLOAD_MAX_RETRY_COUNT):
            for url in self.urls:
                try:
                    self.downloadFile(url)
                    return
                except Exceptions.FileSystemError:
                    raise Exceptions.FileSystemError
                except:
                    pass
        raise Exceptions.NetworkError

    def getFileUrls(self, url, segment, unmute):
        original = Utils.joinUrl(url, segment.fileName)
        unmuted = Utils.joinUrl(url, segment.getUnmutedFileName())
        muted = Utils.joinUrl(url, segment.getMutedFileName())
        if segment.muted:
            if not unmute:
                return [unmuted, muted, original]
        return [original, unmuted, muted]

    def downloadFile(self, url):
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise
        except:
            raise Exceptions.NetworkError
        try:
            with open(self.saveAs, "wb") as file:
                file.write(response.content)
                return
        except:
            raise Exceptions.FileSystemError