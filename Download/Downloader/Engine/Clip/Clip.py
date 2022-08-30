from .FileDownloader import FileDownloader

from Download.Downloader.Engine.Setup import EngineSetup
from Download.Downloader.Engine.ThreadPool import ThreadPool

from Services.Threading.WaitCondition import WaitCondition


class ClipDownloader(EngineSetup):
    def __init__(self, downloadInfo, parent=None):
        super(ClipDownloader, self).__init__(downloadInfo, parent=parent)
        self._doneCondition = WaitCondition(parent=self)

    def download(self):
        self._doneCondition.makeFalse()
        self.task = FileDownloader(
            url=self.setup.downloadInfo.getUrl(),
            saveAs=self.setup.downloadInfo.getAbsoluteFileName(),
            priority=self.setup.priority
        )
        self.task.signals.downloadStarted.connect(self.downloadStarted)
        self.task.signals.downloadProgress.connect(self.downloadProgressHandler)
        self.task.signals.finished.connect(self.downloadFinished)
        ThreadPool.start(self.task, priority=self.task.priority)
        self._doneCondition.wait()
        if self.status.terminateState.isProcessing():
            return
        if not self.result.success:
            raise self.result.error

    def downloadStarted(self, totalByteSize):
        self.progress.totalByteSize = totalByteSize
        self.status.setDownloading()
        self.syncStatus()

    def downloadProgressHandler(self, byteSize):
        self.progress.byteSize = byteSize
        self.syncProgress()

    def downloadFinished(self, task):
        self.result = task.result
        self._doneCondition.makeTrue()

    def cancel(self):
        with self.actionLock:
            if self.isRunning() and not self.status.isDone() and self.status.terminateState.isFalse():
                self.logger.warning("[ACTION] Cancel")
                self.status.terminateState.setProcessing()
                self.syncStatus()
                if ThreadPool.tryTake(self.task):
                    self._doneCondition.makeTrue()
                else:
                    self.task.cancel()