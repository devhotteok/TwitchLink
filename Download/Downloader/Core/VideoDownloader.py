from .BaseDownloader import BaseDownloader
from .Engine.VideoEngine import VideoEngine

from PyQt6 import QtCore


class VideoDownloader(BaseDownloader):
    _pauseRequested = QtCore.pyqtSignal()
    _resumeRequested = QtCore.pyqtSignal()

    def _createEngine(self) -> VideoEngine:
        engine = VideoEngine(
            downloadInfo=self.downloadInfo,
            status=self.status,
            progress=self.progress,
            logger=self.logger,
            parent=None
        )
        self._abortRequested.connect(engine.abort)
        self._pauseRequested.connect(engine.pause)
        self._resumeRequested.connect(engine.resume, QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        return engine

    def pause(self) -> None:
        self.logger.warning("[ACTION] Pause")
        if self.status.pauseState.isFalse() and not self.status.isDone():
            self.status.pauseState.setPreparing()
            self.status.sync()
            self._pauseRequested.emit()

    def resume(self) -> None:
        self.logger.warning("[ACTION] Resume")
        if self.status.pauseState.isTrue() and not self.status.isDone():
            self._resumeRequested.emit()