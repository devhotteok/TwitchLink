from . import Modules

from Services.Utils.MutexLocker import MutexLocker

from PyQt5 import QtCore


class EngineSetup(QtCore.QThread):
    statusUpdate = QtCore.pyqtSignal(Modules.Status)
    progressUpdate = QtCore.pyqtSignal(Modules.Progress)
    dataUpdate = QtCore.pyqtSignal(dict)
    hasUpdate = QtCore.pyqtSignal(object)
    done = QtCore.pyqtSignal(object)

    def __init__(self, downloadInfo, **kwargs):
        super().__init__()
        self.setup = Modules.Setup(downloadInfo, **kwargs)
        self.status = Modules.Status()
        self.progress = Modules.Progress()
        self.actionLock = MutexLocker()
        self.finished.connect(lambda: self.done.emit(self))

    def syncStatus(self):
        self.statusUpdate.emit(self.status)
        self.hasUpdate.emit(self)

    def syncProgress(self):
        self.progressUpdate.emit(self.progress)
        self.hasUpdate.emit(self)

    def syncData(self, data):
        self.dataUpdate.emit(data)
        self.hasUpdate.emit(self)