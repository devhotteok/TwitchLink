from Core import App
from Services.Playlist.Resolution import Resolution
from Download.History import DownloadOptionHistory
from AppData.EncoderDecoder import Serializable


class Exceptions:
    class PreferredResolutionNotFound(Exception):
        def __str__(self):
            return "Preferred Resolution Not Found"


class Quality(Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    def __init__(self, key: int | str):
        self.key = key

    def isValid(self) -> bool:
        return type(self.key) == int

    def toString(self) -> str:
        return f"{self.key}p" if self.isValid() else str(self.key)

    def checkMatch(self, quality: int | str) -> bool:
        return self.key == quality if self.isValid() else False


class FrameRate(Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    def __init__(self, key: int | str):
        self.key = key

    def isValid(self) -> bool:
        return type(self.key) == int

    def toString(self) -> str:
        return str(self.key)

    def checkMatch(self, frameRate: int | str) -> bool:
        return self.key == frameRate if self.isValid() else False


class ScheduledDownloadPreset(Serializable):
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
        def getList(cls) -> tuple[Quality, ...]:
            return cls.BEST, cls.RESOLUTION_1080P, cls.RESOLUTION_720P, cls.RESOLUTION_480P, cls.RESOLUTION_360P, cls.RESOLUTION_160P, cls.WORST, cls.AUDIO_ONLY

    class AVAILABLE_FRAMERATE:
        HIGH = FrameRate("high")
        LOW = FrameRate("low")

        @classmethod
        def getList(cls) -> tuple[FrameRate, ...]:
            return cls.HIGH, cls.LOW

    def __init__(self):
        self.channel = ""
        self.filenameTemplate = self.optionHistory.getFilenameTemplate()
        self.directory = self.optionHistory.getUpdatedDirectory()
        self.preferredQualityIndex = 0
        self.preferredFrameRateIndex = 0
        self.fileFormat = self.getAvailableFormat()
        self.skipAds = self.optionHistory.isSkipAdsEnabled()
        self.remux = self.optionHistory.isRemuxEnabled()
        self.preferredResolutionOnly = False
        self.enabled = True

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def isEnabled(self) -> bool:
        return self.enabled

    @property
    def optionHistory(self) -> DownloadOptionHistory.ScheduledDownloadHistory:
        return App.Preferences.temp.getDownloadOptionHistory(DownloadOptionHistory.ScheduledDownloadHistory)

    def setChannel(self, channel: str) -> None:
        self.channel = channel

    def setDirectory(self, directory: str) -> None:
        self.directory = directory

    def setFilenameTemplate(self, filenameTemplate: str) -> None:
        self.filenameTemplate = filenameTemplate

    def setFileFormat(self, fileFormat: str) -> None:
        self.fileFormat = fileFormat

    def getAvailableFormat(self, currentFormat: str | None = None) -> str:
        availableFormats = self.getAvailableFormats()
        if currentFormat != None:
            if currentFormat in availableFormats:
                return currentFormat
        return availableFormats[0]

    def getAvailableFormats(self) -> list[str]:
        if self.isAudioOnlyPreferred():
            return self.optionHistory.getAvailableAudioFormats()
        else:
            return self.optionHistory.getAvailableFormats()

    def setPreferredQuality(self, index: int) -> None:
        self.preferredQualityIndex = index
        self.setFileFormat(self.getAvailableFormat(self.fileFormat))

    @property
    def preferredQuality(self) -> Quality:
        return self.getQualityList()[self.preferredQualityIndex]

    def getQualityList(self) -> tuple[Quality, ...]:
        return self.AVAILABLE_QUALITY.getList()

    def isAudioOnlyPreferred(self) -> bool:
        return self.preferredQuality == self.AVAILABLE_QUALITY.AUDIO_ONLY

    def setPreferredFrameRate(self, index: int) -> None:
        self.preferredFrameRateIndex = index
        self.setFileFormat(self.getAvailableFormat(self.fileFormat))

    @property
    def preferredFrameRate(self) -> FrameRate:
        return self.getFrameRateList()[self.preferredFrameRateIndex]

    def getFrameRateList(self) -> tuple[FrameRate, ...]:
        return self.AVAILABLE_FRAMERATE.getList()

    def setSkipAdsEnabled(self, enabled: bool) -> None:
        self.skipAds = enabled

    def isSkipAdsEnabled(self) -> bool:
        return self.skipAds

    def setRemuxEnabled(self, enabled: bool) -> None:
        self.remux = enabled

    def isRemuxEnabled(self) -> bool:
        return self.remux

    def setPreferredResolutionOnlyEnabled(self, enabled: bool) -> None:
        self.preferredResolutionOnly = enabled

    def isPreferredResolutionOnlyEnabled(self) -> bool:
        return self.preferredResolutionOnly

    def selectResolution(self, resolutions: list[Resolution]) -> Resolution:
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

    def saveOptionHistory(self) -> None:
        self.optionHistory.setFilenameTemplate(self.filenameTemplate)
        self.optionHistory.setDirectory(self.directory)
        if self.isAudioOnlyPreferred():
            self.optionHistory.setAudioFormat(self.fileFormat)
        else:
            self.optionHistory.setFormat(self.fileFormat)
        self.optionHistory.setSkipAdsEnabled(self.skipAds)
        self.optionHistory.setRemuxEnabled(self.remux)