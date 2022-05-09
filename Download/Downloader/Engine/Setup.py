from . import Modules

from Core.Config import Config
from Services.Utils.Utils import Utils
from Services.Threading.MutexLocker import MutexLocker
from Services.Logging.Logger import Logger
from Services.Logging.ObjectLogger import ObjectLogger

from PyQt5 import QtCore


class EngineSetup(QtCore.QThread):
    needSetup = QtCore.pyqtSignal(object)
    needCleanup = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(Modules.Status)
    progressUpdate = QtCore.pyqtSignal(Modules.Progress)
    dataUpdate = QtCore.pyqtSignal(dict)
    hasUpdate = QtCore.pyqtSignal()

    def __init__(self, downloadInfo, parent=None):
        super(EngineSetup, self).__init__(parent=parent)
        self.setup = Modules.Setup(downloadInfo)
        self.status = Modules.Status()
        self.progress = Modules.Progress()
        self.actionLock = MutexLocker()
        self.setupLogger()

    def getId(self):
        return id(self)

    def setupLogger(self):
        name = f"{Config.APP_NAME}_Download_{self.getId()}"
        self.logger = Logger(
            name=name,
            fileName=f"{name}.txt",
        )
        self.logger.debug(f"{Config.APP_NAME} {Config.VERSION}\n\n[Download Info]\n{ObjectLogger.generateObjectLog(self.setup.downloadInfo)}")

    def run(self):
        self.needSetup.emit(self)
        self.logger.info("Download Started")
        try:
            self.download()
        except Exception as e:
            self.logger.exception(e)
            self.status.raiseError(type(e))
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
        else:
            self.logger.info("Download Completed")
        self.needCleanup.emit(self)

    def download(self):
        pass

    def cancel(self):
        pass

    def syncStatus(self):
        self.statusUpdate.emit(self.status)
        self.hasUpdate.emit()

    def syncProgress(self):
        self.progressUpdate.emit(self.progress)
        self.hasUpdate.emit()

    def syncData(self, data):
        self.dataUpdate.emit(data)
        self.hasUpdate.emit()