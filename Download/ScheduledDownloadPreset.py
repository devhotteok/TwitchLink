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

    def __init__(self, key: str, res: int = 0, fps: int = 0):
        self.key = key
        self.res = res
        self.fps = fps

    def toString(self) -> str:
        return self.key


class ScheduledDownloadPreset(Serializable):
    class AVAILABLE_QUALITY:
        SOURCE = Quality("Source (maximum)")
        RES_1440P60 = Quality("1440p60", 1440, 60)
        RES_1080P60 = Quality("1080p60", 1080, 60)
        RES_720P60 = Quality("720p60", 720, 60)
        RES_480P30 = Quality("480p30", 480, 30)
        RES_360P30 = Quality("360p30", 360, 30)
        RES_160P30 = Quality("160p30", 160, 30)
        AUDIO_ONLY = Quality("Audio Only")

        @classmethod
        def getList(cls) -> tuple[Quality, ...]:
            return cls.SOURCE, cls.RES_1440P60, cls.RES_1080P60, cls.RES_720P60, cls.RES_480P30, cls.RES_360P30, cls.RES_160P30, cls.AUDIO_ONLY

    def __init__(self):
        self.channel = ""
        self.filenameTemplate = self.optionHistory.getFilenameTemplate()
        self.directory = self.optionHistory.getUpdatedDirectory()
        self.preferredQualityIndex = 0
        self.fileFormat = self.getAvailableFormat()
        self.skipAds = self.optionHistory.isSkipAdsEnabled()
        self.remux = self.optionHistory.isRemuxEnabled()
        self.downloadChat = self.optionHistory.isDownloadChatEnabled()
        self.createSubfolderForDownloads = self.optionHistory.isCreateSubfolderForDownloadsEnabled()
        self.preferredResolutionOnly = False
        self.enabled = True

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def isEnabled(self) -> bool:
        return self.enabled
        
    def setDownloadChatEnabled(self, enabled: bool) -> None:
        self.downloadChat = enabled
        
    def isDownloadChatEnabled(self) -> bool:
        return self.downloadChat

    def setCreateSubfolderForDownloadsEnabled(self, enabled: bool) -> None:
        self.createSubfolderForDownloads = enabled

    def isCreateSubfolderForDownloadsEnabled(self) -> bool:
        val = getattr(self, "createSubfolderForDownloads", None)
        if val is not None:
            return val
        return self.optionHistory.isCreateSubfolderForDownloadsEnabled()

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
        if self.preferredQuality == self.AVAILABLE_QUALITY.SOURCE:
            return resolutions[0]
            
        if self.preferredQuality == self.AVAILABLE_QUALITY.AUDIO_ONLY:
            for resolution in reversed(resolutions):
                if resolution.isAudioOnly():
                    return resolution
            for resolution in reversed(resolutions):
                if not resolution.isAudioOnly():
                    return resolution
                    
        req_res = self.preferredQuality.res
        req_fps = self.preferredQuality.fps
        
        for resolution in resolutions:
            res_fps = resolution.frameRate if resolution.frameRate != None else 30
            if resolution.quality == req_res and res_fps == req_fps:
                return resolution
                
        filtered = []
        for res in resolutions:
            if res.isAudioOnly():
                continue
            if res.quality != None and res.quality <= req_res:
                filtered.append(res)
                
        if len(filtered) > 0:
            return max(filtered, key=lambda r: (r.quality or 0, r.frameRate or 0))
            
        videos = [r for r in resolutions if not r.isAudioOnly() and r.quality != None]
        if len(videos) > 0:
            return videos[-1]
            
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
        self.optionHistory.setDownloadChatEnabled(self.downloadChat)
        self.optionHistory.setCreateSubfolderForDownloadsEnabled(getattr(self, "createSubfolderForDownloads", False))