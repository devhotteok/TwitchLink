from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from AppData.EncoderDecoder import Serializable

import os


class BaseOptionHistory:
    @classmethod
    def getId(cls) -> str:
        return cls.__name__


class FileHistory:
    SUPPORTED_FORMATS = [
        ""
    ]

    def __init__(self):
        super().__init__()
        self.setDirectory(Config.DEFAULT_DIRECTORY)
        self.setFormat(self.getAvailableFormats()[0])
        self.createSubfolderForDownloads = None

    def setAbsoluteFileName(self, absoluteFileName: str) -> None:
        self.setDirectory(os.path.dirname(absoluteFileName))
        self.setFormat(os.path.basename(absoluteFileName).rsplit(".", 1)[1])

    def setDirectory(self, directoryHistory: str) -> None:
        self._directory = directoryHistory

    def setFormat(self, formatHistory: str) -> None:
        self._format = formatHistory

    def getDirectory(self) -> str:
        return self._directory

    def getUpdatedDirectory(self) -> str:
        from Core import App
        try:
            default_dir = App.Preferences.general.getDefaultDirectory()
        except Exception:
            default_dir = ""
            
        directories = []
        if default_dir:
            directories.append(default_dir)
        directories.extend([self.getDirectory(), Config.DEFAULT_DIRECTORY, Config.APPDATA_PATH])

        for directory in directories:
            try:
                OSUtils.createDirectory(directory)
                return directory
            except:
                pass
        return self.getDirectory()

    def getFormat(self) -> str:
        return self._format

    def getAvailableFormats(self) -> list[str]:
        return self.SUPPORTED_FORMATS

    def setCreateSubfolderForDownloadsEnabled(self, enabled: bool) -> None:
        self.createSubfolderForDownloads = enabled

    def isCreateSubfolderForDownloadsEnabled(self) -> bool:
        from Core import App
        val = getattr(self, "createSubfolderForDownloads", None)
        if val is not None:
            return val
        return App.Preferences.download.isCreateSubfolderForDownloadsEnabled()


class AudioFormatHistory:
    SUPPORTED_AUDIO_FORMATS = [
        "aac",
        "mp3"
    ]

    def __init__(self):
        super().__init__()
        self.setAudioFormat(self.getAvailableAudioFormats()[0])

    def setAudioFormat(self, audioFormat: str) -> None:
        self._audioFormat = audioFormat

    def getAudioFormat(self) -> str:
        return self._audioFormat

    def getAvailableAudioFormats(self) -> list[str]:
        return self.SUPPORTED_AUDIO_FORMATS


class ChatHistory:
    def __init__(self):
        super().__init__()
        self.setDownloadChatEnabled(False)

    def setDownloadChatEnabled(self, enabled: bool) -> None:
        self.downloadChat = enabled

    def isDownloadChatEnabled(self) -> bool:
        return getattr(self, "downloadChat", False)


class StreamHistory(BaseOptionHistory, FileHistory, AudioFormatHistory, ChatHistory, Serializable):
    SUPPORTED_FORMATS = [
        "ts",
        "mp4",
        "mkv"
    ]

    def __init__(self):
        super().__init__()
        self.setSkipAdsEnabled(True)
        self.setRemuxEnabled(True)

    def setSkipAdsEnabled(self, enabled: bool) -> None:
        self.skipAds = enabled

    def isSkipAdsEnabled(self) -> bool:
        return self.skipAds



    def setRemuxEnabled(self, enabled: bool) -> None:
        self.remux = enabled

    def isRemuxEnabled(self) -> bool:
        return self.remux


class VideoHistory(BaseOptionHistory, FileHistory, AudioFormatHistory, ChatHistory, Serializable):
    SUPPORTED_FORMATS = [
        "ts",
        "mp4",
        "mkv"
    ]

    def __init__(self):
        super().__init__()
        self.setUnmuteVideoEnabled(False)
        self.setUpdateTrackEnabled(False)
        self.setRemuxEnabled(True)

    def setUnmuteVideoEnabled(self, enabled: bool) -> None:
        self._unmuteVideo = enabled

    def setUpdateTrackEnabled(self, enabled: bool) -> None:
        self._updateTrack = enabled

    def setRemuxEnabled(self, enabled: bool) -> None:
        self.remux = enabled

    def isUnmuteVideoEnabled(self) -> bool:
        return self._unmuteVideo

    def isUpdateTrackEnabled(self) -> bool:
        return self._updateTrack

    def isRemuxEnabled(self) -> bool:
        return self.remux


class ClipHistory(BaseOptionHistory, FileHistory, ChatHistory, Serializable):
    SUPPORTED_FORMATS = [
        "mp4",
        "mkv"
    ]


class ThumbnailHistory(BaseOptionHistory, FileHistory, Serializable):
    SUPPORTED_FORMATS = [
        "jpg",
        "png"
    ]


class ScheduledDownloadHistory(StreamHistory):
    def __init__(self):
        super().__init__()
        self.setFilenameTemplate("[{type}] [{channel_name}] [{date}] {title} {resolution}")

    def setFilenameTemplate(self, filenameTemplate: str) -> None:
        self._filenameTemplate = filenameTemplate

    def getFilenameTemplate(self) -> str:
        return self._filenameTemplate