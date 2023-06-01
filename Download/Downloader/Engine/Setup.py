from . import Modules

from Core.Config import Config
from Services.Utils.Utils import Utils
from Services.FileNameManager import FileNameManager
from Services.Threading.MutexLocker import MutexLocker
from Services.Logging.Logger import Logger
from Services.Logging.ObjectLogger import ObjectLogger

from PyQt6 import QtCore

import uuid


class EngineSetup(QtCore.QThread):
    started = QtCore.pyqtSignal(object)
    finished = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(Modules.Status)
    progressUpdate = QtCore.pyqtSignal(Modules.Progress)
    dataUpdate = QtCore.pyqtSignal(dict)
    hasUpdate = QtCore.pyqtSignal()

    def __init__(self, downloadInfo, parent=None):
        super(EngineSetup, self).__init__(parent=parent)
        self.uuid = uuid.uuid4()
        self.setup = Modules.Setup(downloadInfo)
        self.status = Modules.Status()
        self.progress = Modules.Progress()
        self.actionLock = MutexLocker()
        self.setupLogger()
        super().started.connect(self.emitStartedSignal)
        super().finished.connect(self.emitFinishedSignal)

    def emitStartedSignal(self):
        self.started.emit(self)

    def emitFinishedSignal(self):
        self.finished.emit(self)

    def getId(self):
        return self.uuid

    def setupLogger(self):
        self.logger = Logger(
            name=f"Downloader_{self.getId()}",
            fileName=f"{Config.APP_NAME}_Download_{Logger.getFormattedTime()}#{self.getId()}.log"
        )
        self.logger.debug(f"{Config.APP_NAME} {Config.APP_VERSION}\n\n[Download Info]\n{ObjectLogger.generateObjectLog(self.setup.downloadInfo)}")

    def run(self):
        self.logger.info("Download Started")
        try:
            with FileNameManager.lock(self.setup.downloadInfo.getAbsoluteFileName()):
                self.download()
        except Exception as e:
            self.logger.exception(e)
            self.status.raiseError(e)
        with self.actionLock:
            if self.status.terminateState.isProcessing():
                if not self.setup.downloadInfo.type.isStream() and self.status.getError() == None:
                    try:
                        Utils.removeFile(self.setup.downloadInfo.getAbsoluteFileName())
                    except:
                        pass
                self.status.terminateState.setTrue()
            self.status.setDone()
            self.syncStatus()
        if self.status.terminateState.isTrue():
            if self.status.getError() == None:
                if self.setup.downloadInfo.type.isStream():
                    self.logger.info("Download Stopped")
                else:
                    self.logger.info("Download Canceled")
            else:
                self.logger.info("Download Failed")
                self.logger.warning("Download failed for the following reason.")
                self.logger.exception(self.status.getError())
        else:
            self.logger.info("Download Completed")

    def download(self):
        pass

    def cancel(self):
        pass

    def abort(self, exception):
        self.logger.warning("Abort requested with the following exception.")
        self.logger.warning(exception)
        self.cancel()
        self.status.raiseError(exception)

    def syncStatus(self):
        self.statusUpdate.emit(self.status)
        self.hasUpdate.emit()

    def syncProgress(self):
        self.progressUpdate.emit(self.progress)
        self.hasUpdate.emit()

    def syncData(self, data):
        self.dataUpdate.emit(data)
        self.hasUpdate.emit()