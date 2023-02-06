from Database.Database import DB
from Database.EncoderDecoder import Codable
from Download import DownloadOptionHistory

import copy


class Exceptions:
    class PreferredResolutionNotFound(Exception):
        def __str__(self):
            return "Preferred Resolution Not Found"


class Quality(Codable):
    CODABLE_INIT_MODEL = False
    CODABLE_STRICT_MODE = False

    def __init__(self, key):
        self.key = key

    def isValid(self):
        return type(self.key) == int

    def toString(self):
        return f"{self.key}p" if self.isValid() else str(self.key)

    def checkMatch(self, quality):
        return self.key == quality if self.isValid() else False


class FrameRate(Codable):
    CODABLE_INIT_MODEL = False
    CODABLE_STRICT_MODE = False

    def __init__(self, key):
        self.key = key

    def isValid(self):
        return type(self.key) == int

    def toString(self):
        return str(self.key)

    def checkMatch(self, frameRate):
        return self.key == frameRate if self.isValid() else False


class ScheduledDownloadPreset(Codable):
    class AVAILABLE_QUALITY:
        BEST = Quality("best")
        RESOLUTION_1080P = Quality(1080)
        RESOLUTION_720P = Quality(720)
        RESOLUTION_480P = Quality(480)
        RESOLUTION_360P = Quality(360)
        RESOLUTION_160P = Quality(160)
        WORST = Quality("worst")
        AUDIO_ONLY = Quality("audio-only")

        @classmethod
        def getList(cls):
            return [cls.BEST, cls.RESOLUTION_1080P, cls.RESOLUTION_720P, cls.RESOLUTION_480P, cls.RESOLUTION_360P, cls.RESOLUTION_160P, cls.WORST, cls.AUDIO_ONLY]

    class AVAILABLE_FRAMERATE:
        HIGH = FrameRate("high")
        LOW = FrameRate("low")

        @classmethod
        def getList(cls):
            return [cls.HIGH, cls.LOW]

    def __init__(self):
        self.channel = ""
        self.filenameTemplate = self.optionHistory.getFilenameTemplate()
        self.directory = self.optionHistory.getUpdatedDirectory()
        self.preferredQualityIndex = 0
        self.preferredFrameRateIndex = 0
        self.fileFormat = self.getAvailableFormat()
        self.preferredResolutionOnly = False
        self.enabled = True

    def setEnabled(self, enabled):
        self.enabled = enabled

    def isEnabled(self):
        return self.enabled

    @property
    def optionHistory(self):
        return DB.temp.getDownloadOptionHistory(DownloadOptionHistory.ScheduledDownloadHistory)

    def setChannel(self, channel):
        self.channel = channel

    def setDirectory(self, directory):
        self.directory = directory

    def setFilenameTemplate(self, filenameTemplate):
        self.filenameTemplate = filenameTemplate

    def setFileFormat(self, fileFormat):
        self.fileFormat = fileFormat

    def getAvailableFormat(self, currentFormat=None):
        availableFormats = self.getAvailableFormats()
        if currentFormat != None:
            if currentFormat in availableFormats:
                return currentFormat
        return availableFormats[0]

    def getAvailableFormats(self):
        if self.isAudioOnlyPreferred():
            return self.optionHistory.getAvailableAudioFormats()
        else:
            return self.optionHistory.getAvailableFormats()

    def setPreferredQuality(self, index):
        self.preferredQualityIndex = index
        self.setFileFormat(self.getAvailableFormat(self.fileFormat))

    @property
    def preferredQuality(self):
        return self.getQualityList()[self.preferredQualityIndex]

    def getQualityList(self):
        return self.AVAILABLE_QUALITY.getList()

    def isAudioOnlyPreferred(self):
        return self.preferredQuality == self.AVAILABLE_QUALITY.AUDIO_ONLY

    def setPreferredFrameRate(self, index):
        self.preferredFrameRateIndex = index
        self.setFileFormat(self.getAvailableFormat(self.fileFormat))

    @property
    def preferredFrameRate(self):
        return self.getFrameRateList()[self.preferredFrameRateIndex]

    def getFrameRateList(self):
        return self.AVAILABLE_FRAMERATE.getList()

    def setPreferredResolutionOnlyEnabled(self, enabled):
        self.preferredResolutionOnly = enabled

    def isPreferredResolutionOnlyEnabled(self):
        return self.preferredResolutionOnly

    def selectResolution(self, resolutions):
        if self.preferredQuality == self.AVAILABLE_QUALITY.BEST:
            return resolutions[0]
        elif self.preferredQuality == self.AVAILABLE_QUALITY.WORST:
            for resolution in reversed(resolutions):
                if not resolution.isAudioOnly():
                    return resolution
        elif self.preferredQuality == self.AVAILABLE_QUALITY.AUDIO_ONLY:
            for resolution in reversed(resolutions):
                if resolution.isAudioOnly():
                    return resolution
        else:
            matchingResolutions = []
            for resolution in resolutions:
                if self.preferredQuality.checkMatch(resolution.quality):
                    matchingResolutions.append(resolution)
            if len(matchingResolutions) != 0:
                if self.preferredFrameRate == self.AVAILABLE_FRAMERATE.HIGH:
                    return matchingResolutions[0]
                else:
                    return matchingResolutions[-1]
        if self.isPreferredResolutionOnlyEnabled():
            raise Exceptions.PreferredResolutionNotFound
        return resolutions[0]

    def saveOptionHistory(self):
        self.optionHistory.setFilenameTemplate(self.filenameTemplate)
        self.optionHistory.setDirectory(self.directory)
        if self.isAudioOnlyPreferred():
            self.optionHistory.setAudioFormat(self.fileFormat)
        else:
            self.optionHistory.setFormat(self.fileFormat)

    def copy(self):
        return copy.deepcopy(self)