from .Config import Config

from Services.Utils.SystemUtils import SystemUtils


class Setup:
    def __init__(self, downloadInfo):
        self.downloadInfo = downloadInfo
        if self.downloadInfo.type.isVideo():
            self.unmuteVideo = self.downloadInfo.isUnmuteVideoEnabled()
            self.updateTrack = self.downloadInfo.isUpdateTrackEnabled()
            self.priority = (1 if self.downloadInfo.isPrioritizeEnabled() else 0) * 2
        elif self.downloadInfo.type.isClip():
            self.priority = (1 if self.downloadInfo.isPrioritizeEnabled() else 0) * 2


class State:
    STATE_FALSE = 0
    STATE_PROCESSING = 1
    STATE_TRUE = 2

    def __init__(self, state=STATE_FALSE):
        self._state = state

    def setFalse(self):
        self._state = self.STATE_FALSE

    def isFalse(self):
        return self._state == self.STATE_FALSE

    def setProcessing(self):
        self._state = self.STATE_PROCESSING

    def isProcessing(self):
        return self._state == self.STATE_PROCESSING

    def setTrue(self):
        self._state = self.STATE_TRUE

    def isTrue(self):
        return self._state == self.STATE_TRUE


class Status:
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    WAITING = "waiting"
    UPDATING = "updating"
    ENCODING = "encoding"
    DONE = "done"

    def __init__(self):
        self.pauseState = State()
        self.terminateState = State()
        self._status = Status.PREPARING
        self._waitingCount = 0
        self._waitingTime = None
        self._updateFound = False
        self._skipWaiting = False
        self._skipDownload = False
        self._error = None

    def isPreparing(self):
        return self._status == Status.PREPARING

    def setDownloading(self):
        self._status = Status.DOWNLOADING

    def isDownloading(self):
        return self._status == Status.DOWNLOADING

    def setWaiting(self):
        self._status = Status.WAITING

    def isWaiting(self):
        return self._status == Status.WAITING

    def setWaitingCount(self, waitingCount):
        self._waitingCount = waitingCount

    def getWaitingCount(self):
        return self._waitingCount

    def getMaxWaitingCount(self):
        return Config.UPDATE_TRACK_MAX_RETRY_COUNT

    def setWaitingTime(self, waitingTime):
        self._waitingTime = waitingTime

    def getWaitingTime(self):
        return self._waitingTime

    def setUpdating(self):
        self._status = Status.UPDATING

    def isUpdating(self):
        return self._status == Status.UPDATING

    def setEncoding(self):
        self._status = Status.ENCODING

    def isEncoding(self):
        return self._status == Status.ENCODING

    def setDone(self):
        self._status = Status.DONE

    def isDone(self):
        return self._status == Status.DONE

    def setUpdateFound(self):
        self._updateFound = True

    def isUpdateFound(self):
        return self._updateFound

    def setSkipWaiting(self, skipWaiting):
        self._skipWaiting = skipWaiting

    def isWaitingSkipped(self):
        return self._skipWaiting

    def setDownloadSkip(self):
        self._skipDownload = True

    def isDownloadSkipped(self):
        return self._skipDownload

    def raiseError(self, error):
        self._error = error
        self.terminateState.setProcessing()

    def getError(self):
        return self._error


class Progress:
    def __init__(self):
        self.file = 0
        self.totalFiles = 0
        self.mutedFiles = 0
        self.missingFiles = 0
        self.milliseconds = 0
        self.totalMilliseconds = 0
        self.mutedMilliseconds = 0
        self.missingMilliseconds = 0
        self.byteSize = 0
        self.totalByteSize = 0

    @staticmethod
    def getPercentage(part, whole):
        return (part / (whole or 1)) * 100

    @property
    def fileProgress(self):
        return self.getPercentage(self.file, self.totalFiles)

    @property
    def timeProgress(self):
        return self.getPercentage(self.seconds, self.totalSeconds)

    @property
    def seconds(self):
        return self.milliseconds / 1000

    @property
    def totalSeconds(self):
        return self.totalMilliseconds / 1000

    @property
    def mutedSeconds(self):
        return self.mutedMilliseconds / 1000

    @property
    def missingSeconds(self):
        return self.missingMilliseconds / 1000

    @property
    def size(self):
        return SystemUtils.formatByteSize(self.byteSize)

    @property
    def totalSize(self):
        return SystemUtils.formatByteSize(self.totalByteSize)

    @property
    def sizeProgress(self):
        return self.getPercentage(self.byteSize, self.totalByteSize)