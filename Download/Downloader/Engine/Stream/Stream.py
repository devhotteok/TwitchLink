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
            self.FFmpeg.startEncodingProcess(
                target=self.setup.downloadInfo.getUrl(),
                saveAs=self.setup.downloadInfo.getAbsoluteFileName(),
                remux=True,
                logLevel=FFmpeg.LogLevel.WARNING,
                priority=FFmpeg.Priority.HIGH
            )
        self.status.setDownloading()
        self.syncStatus()
        for progress in self.FFmpeg.output(logger=self.logger):
            time = progress.get("time")
            if time != None:
                self.progress.milliseconds = Utils.toSeconds(*time.split(".")[0].split(":")) * 1000 + int(time.split(".")[1][:3])
            size = progress.get("size") or progress.get("Lsize")
            if size != None:
                self.progress.totalByteSize = Utils.getByteSize(size)
                self.progress.byteSize = self.progress.totalByteSize
            self.syncProgress()

    def cancel(self):
        with self.actionLock:
            if self.isRunning() and not self.status.isDone() and self.status.terminateState.isFalse():
                self.logger.warning("[ACTION] Cancel")
                self.status.terminateState.setProcessing()
                self.syncStatus()
                if self.FFmpeg != None:
                    self.FFmpeg.kill()