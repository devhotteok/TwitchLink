from Services.Utils.Utils import Utils
from Database.Database import DB
from Database.EncoderDecoder import Codable
from Download import DownloadOptionHistory
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator

import os
import copy


class DownloadInfo(Codable):
    CODABLE_INIT_MODEL = False
    CODABLE_STRICT_MODE = False

    def __init__(self, videoData, accessToken):
        self.videoData = videoData
        self.accessToken = accessToken
        if self.type.isStream():
            self.stream = videoData
        elif self.type.isVideo():
            self.video = videoData
            self.range = [None, None]
            self.unmuteVideo = self.optionHistory.isUnmuteVideoEnabled()
            self.updateTrack = self.optionHistory.isUpdateTrackEnabled()
            self.clippingMode = False
            self.prioritize = False
        else:
            self.clip = videoData
            self.prioritize = False
        self.directory = self.optionHistory.getUpdatedDirectory()
        self.selectedResolutionIndex = 0
        self.fileName = self.generateFileName()
        self.fileFormat = self.getAvailableFormat()

    def setAccessToken(self, accessToken):
        self.accessToken = accessToken
        self.setResolution(min(self.selectedResolutionIndex, len(self.accessToken.resolutions) - 1))

    @property
    def type(self):
        return self.accessToken.type

    def getRangeInSeconds(self):
        start, end = self.range
        return (None if start == None else start / 1000, None if end == None else end / 1000)

    @property
    def optionHistory(self):
        if self.type.isStream():
            historyType = DownloadOptionHistory.StreamHistory
        elif self.type.isVideo():
            historyType = DownloadOptionHistory.VideoHistory
        else:
            historyType = DownloadOptionHistory.ClipHistory
        return DB.temp.getDownloadOptionHistory(historyType)

    def generateFileName(self):
        return FileNameGenerator.generateFileName(self.videoData, self.resolution)

    def setResolution(self, index):
        self.selectedResolutionIndex = index
        self.setFileFormat(self.getAvailableFormat(self.fileFormat))

    @property
    def resolution(self):
        return self.accessToken.getResolutions()[self.selectedResolutionIndex]

    def getAvailableFormat(self, currentFormat=None):
        defaultFormat = self.optionHistory.getAudioFormat() if self.resolution.isAudioOnly() else self.optionHistory.getFormat()
        availableFormats = self.getAvailableFormats()
        if currentFormat != None:
            if currentFormat in availableFormats:
                return currentFormat
        return defaultFormat if defaultFormat in availableFormats else availableFormats[0]

    def getAvailableFormats(self):
        if self.resolution.isAudioOnly():
            return self.optionHistory.getAvailableAudioFormats()
        else:
            return self.optionHistory.getAvailableFormats()

    def setCropRange(self, start, end):
        self.range = [start, end]

    def setDirectory(self, directory):
        self.directory = directory

    def setAbsoluteFileName(self, absoluteFileName):
        self.directory = os.path.dirname(absoluteFileName)
        self.fileName, self.fileFormat = os.path.basename(absoluteFileName).rsplit(".", 1)

    def setFileName(self, fileName):
        self.fileName = fileName

    def setFileFormat(self, fileFormat):
        self.fileFormat = fileFormat

    def setUnmuteVideoEnabled(self, unmuteVideo):
        self.unmuteVideo = unmuteVideo

    def setUpdateTrackEnabled(self, updateTrack):
        self.updateTrack = updateTrack

    def setClippingModeEnabled(self, clippingMode):
        self.clippingMode = clippingMode

    def setPrioritizeEnabled(self, prioritize):
        self.prioritize = prioritize

    def isUnmuteVideoEnabled(self):
        return self.unmuteVideo

    def isUpdateTrackEnabled(self):
        return self.updateTrack

    def isClippingModeEnabled(self):
        return self.clippingMode

    def isPrioritizeEnabled(self):
        return self.prioritize

    def saveOptionHistory(self):
        self.optionHistory.setDirectory(self.directory)
        if self.resolution.isAudioOnly():
            self.optionHistory.setAudioFormat(self.fileFormat)
        else:
            self.optionHistory.setFormat(self.fileFormat)
        if self.type.isVideo():
            self.optionHistory.setUnmuteVideoEnabled(self.unmuteVideo)
            self.optionHistory.setUpdateTrackEnabled(self.updateTrack)

    def getUrl(self):
        return self.resolution.url

    def getAbsoluteFileName(self):
        return f"{Utils.joinPath(self.directory, self.fileName)}.{self.fileFormat}"

    def copy(self):
        return copy.deepcopy(self)