from Core.GlobalExceptions import Exceptions
from Services.NetworkRequests import Network
from Services.Utils.Utils import Utils
from Download.Downloader.Engine.Config import Config
from Services.Task.PrioritizedTask import PrioritizedTask


class SegmentUrl:
    def __init__(self, url, muted=False):
        self.url = url
        self.muted = muted


class SegmentDownloader(PrioritizedTask):
    def __init__(self, url, segment, unmute, saveAs, priority=0):
        super(SegmentDownloader, self).__init__(priority=priority)
        self.url = url
        self.segment = segment
        self.unmute = unmute
        self.segmentUrls = self.getFileUrls()
        self.saveAs = saveAs

    def task(self):
        for i in range(Config.SEGMENT_DOWNLOAD_MAX_RETRY_COUNT):
            for segmentUrl in self.segmentUrls:
                try:
                    self.downloadFile(segmentUrl.url)
                    return segmentUrl
                except Exceptions.FileSystemError:
                    raise Exceptions.FileSystemError
                except:
                    pass
        raise Exceptions.NetworkError

    def getFileUrls(self):
        original = SegmentUrl(url=Utils.joinUrl(self.url, self.segment.fileName), muted=False)
        unmuted = SegmentUrl(url=Utils.joinUrl(self.url, self.segment.getUnmutedFileName()), muted=False)
        muted = SegmentUrl(url=Utils.joinUrl(self.url, self.segment.getMutedFileName()), muted=True)
        if self.segment.muted:
            if not self.unmute:
                return [unmuted, muted, original]
        return [original, unmuted, muted]

    def downloadFile(self, url):
        try:
            response = Network.session.get(url, timeout=(10, 60))
            if response.status_code != 200:
                raise
        except:
            raise Exceptions.NetworkError
        try:
            with open(self.saveAs, "wb") as file:
                file.write(response.content)
        except:
            raise Exceptions.FileSystemError