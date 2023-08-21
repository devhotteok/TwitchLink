from .Config import Config

from Services.Utils.Utils import Utils

from PyQt6 import QtCore

import enum


class State(QtCore.QObject):
    class Types(enum.Enum):
        FALSE = 0
        PREPARING = 1
        PROCESSING = 2
        TRUE = 3

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._state = self.Types.FALSE

    def setFalse(self) -> None:
        self._state = self.Types.FALSE

    def isFalse(self) -> bool:
        return self._state == self.Types.FALSE

    def setPreparing(self) -> None:
        self._state = self.Types.PREPARING

    def isPreparing(self) -> bool:
        return self._state == self.Types.PREPARING

    def setProcessing(self) -> None:
        self._state = self.Types.PROCESSING

    def isProcessing(self) -> bool:
        return self._state == self.Types.PROCESSING

    def isInProgress(self) -> bool:
        return self._state == self.Types.PREPARING or self._state == self.Types.PROCESSING

    def setTrue(self) -> None:
        self._state = self.Types.TRUE

    def isTrue(self) -> bool:
        return self._state == self.Types.TRUE


class Status(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    DONE = "done"

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.pauseState = State(parent=self)
        self.terminateState = State(parent=self)
        self._status = Status.PREPARING
        self._nextUpdate: QtCore.QDateTime | None = None
        self._waitingCount = 0
        self._error = None
        self._fileRemoved = False

    def isPreparing(self) -> bool:
        return self._status == Status.PREPARING

    def setDownloading(self) -> None:
        self._status = Status.DOWNLOADING

    def isDownloading(self) -> bool:
        return self._status == Status.DOWNLOADING

    def setNextUpdateDateTime(self, nextUpdate: QtCore.QDateTime | None) -> None:
        self._nextUpdate = nextUpdate

    def getNextUpdateDateTime(self) -> QtCore.QDateTime | None:
        return self._nextUpdate

    def setWaitingCount(self, waitingCount: int) -> None:
        self._waitingCount = waitingCount

    def getWaitingCount(self) -> int:
        return self._waitingCount

    def getMaxWaitingCount(self) -> int:
        return Config.UPDATE_TRACK_MAX_RETRY_COUNT

    def setDone(self) -> None:
        self._status = Status.DONE

    def isDone(self) -> bool:
        return self._status == Status.DONE

    def raiseError(self, error: Exception) -> None:
        if self._error == None:
            self._error = error
            self.terminateState.setProcessing()

    def getError(self) -> Exception | None:
        return self._error

    def setFileRemoved(self) -> None:
        self._fileRemoved = True

    def isFileRemoved(self) -> bool:
        return self._fileRemoved

    def sync(self) -> None:
        self.updated.emit()


class Progress(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.files = 0
        self.totalFiles = 0
        self.mutedFiles = 0
        self.skippedFiles = 0
        self.missingFiles = 0
        self.milliseconds = 0
        self.totalMilliseconds = 0
        self.mutedMilliseconds = 0
        self.skippedMilliseconds = 0
        self.missingMilliseconds = 0
        self.byteSize = 0
        self.totalByteSize = 0

    @staticmethod
    def _getPercentage(part: float, whole: float) -> int:
        return int((part / (whole or 1)) * 100)

    @property
    def fileProgress(self) -> int:
        return self._getPercentage(self.files, self.totalFiles)

    @property
    def timeProgress(self) -> int:
        return self._getPercentage(self.milliseconds, self.totalMilliseconds)

    @property
    def sizeProgress(self) -> int:
        return self._getPercentage(self.byteSize, self.totalByteSize)

    @property
    def size(self) -> str:
        return Utils.formatByteSize(self.byteSize)

    @property
    def totalSize(self) -> str:
        return Utils.formatByteSize(self.totalByteSize)

    def sync(self) -> None:
        self.updated.emit()