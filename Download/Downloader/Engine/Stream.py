from .Setup import EngineSetup

from Services.Utils.Utils import Utils
from Download.Downloader.FFmpeg.FFmpeg import FFmpeg


class StreamDownloader(EngineSetup):
    def __init__(self, downloadInfo, **kwargs):
        super().__init__(downloadInfo, **kwargs)
        self.FFmpeg = None

    def run(self):
        try:
            self.download()
        except Exception as e:
            self.status.raiseError(type(e))
        with self.actionLock:
            if self.status.terminateState.isProcessing():
                self.status.terminateState.setTrue()
            self.status.setDone()
            self.syncStatus()

    def download(self):
        with self.actionLock:
            if self.status.terminateState.isProcessing():
                return
            self.FFmpeg = FFmpeg(self.setup.downloadInfo.getUrl(), self.setup.downloadInfo.getAbsoluteFileName())
        self.status.setDownloading()
        self.syncStatus()
        for progress in self.FFmpeg.output():
            time = progress.get("time")
            if time != None:
                self.progress.seconds = Utils.toSeconds(*time.split(".")[0].split(":"))
            size = progress.get("size") or progress.get("Lsize")
            if size != None:
                self.progress.totalSize = Utils.formatByteSize(size)
                self.progress.size = self.progress.totalSize
            self.syncProgress()

    def cancel(self):
        with self.actionLock:
            if self.isRunning() and not self.status.isDone() and self.status.terminateState.isFalse():
                self.status.terminateState.setProcessing()
                self.syncStatus()
                if self.FFmpeg != None:
                    self.FFmpeg.kill()