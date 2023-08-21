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
        for directory in [self.getDirectory(), Config.DEFAULT_DIRECTORY, Config.APPDATA_PATH]:
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


class StreamHistory(BaseOptionHistory, FileHistory, AudioFormatHistory, Serializable):
    SUPPORTED_FORMATS = [
        "ts",
        "mp4"
    ]

    def __init__(self):
        super().__init__()
        self.setRemuxEnabled(True)

    def setRemuxEnabled(self, enabled: bool) -> None:
        self.remux = enabled

    def isRemuxEnabled(self) -> bool:
        return self.remux


class VideoHistory(BaseOptionHistory, FileHistory, AudioFormatHistory, Serializable):
    SUPPORTED_FORMATS = [
        "ts",
        "mp4"
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


class ClipHistory(BaseOptionHistory, FileHistory, Serializable):
    SUPPORTED_FORMATS = [
        "mp4"
    ]


class ThumbnailHistory(BaseOptionHistory, FileHistory, Serializable):
    SUPPORTED_FORMATS = [
        "jpg",
        "png"
    ]


class ScheduledDownloadHistory(BaseOptionHistory, FileHistory, AudioFormatHistory, Serializable):
    SUPPORTED_FORMATS = [
        "ts",
        "mp4"
    ]

    def __init__(self):
        super().__init__()
        self.setFilenameTemplate("[{type}] [{channel_name}] [{date}] {title} {resolution}")

    def setFilenameTemplate(self, filenameTemplate: str) -> None:
        self._filenameTemplate = filenameTemplate

    def getFilenameTemplate(self) -> str:
        return self._filenameTemplate