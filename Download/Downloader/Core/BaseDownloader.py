from .Engine import Modules
from .Engine.BaseEngine import BaseEngine
from .Engine.ChatEngine import ChatEngine

from Core.Config import Config
from Core.GlobalExceptions import Exceptions
from Download.DownloadInfo import DownloadInfo
from Services.Logging.Logger import Logger
from Services.FileNameLocker import FileNameLocker

from PyQt6 import QtCore

import uuid


class BaseDownloader(QtCore.QThread):
    started = QtCore.pyqtSignal(object)
    finished = QtCore.pyqtSignal(object)
    _abortRequested = QtCore.pyqtSignal(Exception)
    _finishEarlyRequested = QtCore.pyqtSignal()

    def __init__(self, downloadInfo: DownloadInfo, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.uuid = uuid.uuid4()
        self.downloadInfo = downloadInfo
        self.isFinishingEarly = False
        self.status = Modules.Status(parent=self)
        self.progress = Modules.Progress(parent=self)
        self.logger = Logger(
            name=f"Downloader_{self.getId()}",
            fileName=f"{Config.APP_NAME}_Download_{Logger.getFormattedTime()}#{self.getId()}.log"
        )
        absoluteFileName = self.downloadInfo.getAbsoluteFileName()
        if self.downloadInfo.isCreateSubfolderForDownloadsEnabled():
            from Services.Utils.OSUtils import OSUtils
            import os
            directory = os.path.dirname(absoluteFileName)
            if not OSUtils.isDirectory(directory):
                OSUtils.createDirectory(directory)
        self._fileNameLocker = FileNameLocker(absoluteFileName)
        self._fileNameLocker.lock()
        super().started.connect(self._threadStarted)
        super().finished.connect(self._threadFinished)

    def getId(self) -> uuid.UUID:
        return self.uuid

    def _threadStarted(self) -> None:
        self.started.emit(self)

    def _threadFinished(self) -> None:
        self._fileNameLocker.unlock()
        self.finished.emit(self)

    def _createEngine(self) -> BaseEngine:
        engine = BaseEngine(
            downloadInfo=self.downloadInfo,
            status=self.status,
            progress=self.progress,
            logger=self.logger,
            parent=None
        )
        self._abortRequested.connect(engine.abort)
        return engine

    def run(self) -> None:
        engine = self._createEngine()
        chatEngine = ChatEngine(self.downloadInfo, self.logger, parent=None)
        
        from Download.Downloader.Core.ChatRecoveryManager import ChatRecoveryManager
        import os
        chatRecoveryManager = ChatRecoveryManager(self.logger)
        def _saveRecovery():
            if getattr(self.downloadInfo, "downloadChat", False):
                videoFilePath = self.downloadInfo.getAbsoluteFileName()
                chatFilePath = os.path.splitext(videoFilePath)[0] + ".json"
                isLivestream = self.downloadInfo.type.isStream()
                chatRecoveryManager.saveRecoveryState(str(self.uuid), chatFilePath, isLivestream, self.progress.downloadedTimeline)
                
        self.progress.updated.connect(_saveRecovery)
        
        self._abortRequested.connect(lambda e: chatEngine.abort(cleanUp=False))
        engine.finished.connect(lambda: chatEngine.abort(cleanUp=False))
        engine.finished.connect(lambda: chatEngine.postProcess(self.progress.downloadedTimeline))
        engine.finished.connect(lambda: chatRecoveryManager.removeRecoveryState(str(self.uuid)))
        engine.finished.connect(self.exit)
        
        chatEngine.start()
        engine.start()
        self.exec()
        engine.deleteLater()
        chatEngine.deleteLater()

    def cancel(self) -> None:
        self.logger.warning("[ACTION] Cancel")
        self.abort(Exceptions.AbortRequested())

    def finishEarly(self) -> None:
        if self.status.terminateState.isFalse() and not self.status.isDone():
            self.logger.warning("[ACTION] Finish Early")
            self.isFinishingEarly = True
            self.status.raiseError(Exceptions.AbortRequested())
            self.status.sync()
            self._finishEarlyRequested.emit()

    def abort(self, exception: Exception) -> None:
        if self.status.terminateState.isFalse() and not self.status.isDone():
            self.status.terminateState.setPreparing()
            self.status.sync()
            self._abortRequested.emit(exception)