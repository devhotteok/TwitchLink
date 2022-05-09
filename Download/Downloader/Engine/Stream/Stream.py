from Download.Downloader.Engine.Setup import EngineSetup

from Services.Utils.Utils import Utils
from Download.Downloader.FFmpeg.FFmpeg import FFmpeg


class StreamDownloader(EngineSetup):
    def __init__(self, downloadInfo, parent=None):
        super(StreamDownloader, self).__init__(downloadInfo, parent=parent)
        self.FFmpeg = FFmpeg(parent=self)

    def download(self):
        with self.actionLock:
            if self.status.terminateState.isProcessing():
                return
            self.FFmpeg.start(self.setup.downloadInfo.getUrl(), self.setup.downloadInfo.getAbsoluteFileName(), logLevel=FFmpeg.LogLevel.WARNING, priority=FFmpeg.Priority.HIGH)
        self.status.setDownloading()
        self.syncStatus()
        for progress in self.FFmpeg.output(logger=self.logger):
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
                self.logger.warning("[ACTION] Cancel")
                self.status.terminateState.setProcessing()
                self.syncStatus()
                if self.FFmpeg != None:
                    self.FFmpeg.kill()