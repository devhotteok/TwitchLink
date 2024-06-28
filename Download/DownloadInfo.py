from Core import App
from Services.Utils.Utils import Utils
from Services.Twitch.GQL.TwitchGQLModels import Stream, Video, Clip
from Services.Twitch.Playback.TwitchPlaybackModels import TwitchStreamPlayback, TwitchVideoPlayback, TwitchClipPlayback
from Services.Playlist.Resolution import Resolution
from Download.History.DownloadOptionHistory import StreamHistory, VideoHistory, ClipHistory
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator
from AppData.EncoderDecoder import Serializable

from PyQt6 import QtCore

import enum
import os


class DownloadInfoType:
    class Types(enum.Enum):
        STREAM = "stream"
        VIDEO = "video"
        CLIP = "clip"

    def __init__(self, type: Types):
        self._type = type.value

    def isStream(self) -> bool:
        return self._type == self.Types.STREAM.value

    def isVideo(self) -> bool:
        return self._type == self.Types.VIDEO.value

    def isClip(self) -> bool:
        return self._type == self.Types.CLIP.value

    def toString(self) -> str:
        return self._type


class DownloadInfo(Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    def __init__(self, content: Stream | Video | Clip, playback: TwitchStreamPlayback | TwitchVideoPlayback | TwitchClipPlayback):
        self.content = content
        self.playback = playback
        if self.type.isStream():
            self.skipAds = False if self.playback.token.hideAds else self.optionHistory.isSkipAdsEnabled()
            self.remux = self.optionHistory.isRemuxEnabled()
        elif self.type.isVideo():
            self.range = (None, None)
            self.unmuteVideo = self.optionHistory.isUnmuteVideoEnabled()
            self.updateTrack = self.optionHistory.isUpdateTrackEnabled()
            self.prioritize = False
            self.remux = self.optionHistory.isRemuxEnabled()
        elif self.type.isClip():
            self.prioritize = False
        self.directory = self.optionHistory.getUpdatedDirectory()
        self.selectedResolutionIndex = 0
        self.fileName = self.generateFileName()
        self.fileFormat = self.getAvailableFormat()

    def updateContent(self, content: Stream | Video | Clip) -> None:
        self.content = content

    def updatePlayback(self, playback: TwitchStreamPlayback | TwitchVideoPlayback | TwitchClipPlayback) -> None:
        self.playback = playback
        if isinstance(self.playback, TwitchStreamPlayback) and self.playback.token.hideAds:
            self.skipAds = False
        self.setResolution(min(self.selectedResolutionIndex, len(self.playback.resolutions) - 1))

    @property
    def type(self) -> DownloadInfoType:
        if isinstance(self.content, Stream):
            return DownloadInfoType(DownloadInfoType.Types.STREAM)
        elif isinstance(self.content, Video):
            return DownloadInfoType(DownloadInfoType.Types.VIDEO)
        else:
            return DownloadInfoType(DownloadInfoType.Types.CLIP)

    def getCropRangeMilliseconds(self) -> tuple[int | None, int | None]:
        return self.range

    @property
    def optionHistory(self) -> StreamHistory | VideoHistory | ClipHistory:
        if self.type.isStream():
            historyType = StreamHistory
        elif self.type.isVideo():
            historyType = VideoHistory
        else:
            historyType = ClipHistory
        return App.Preferences.temp.getDownloadOptionHistory(historyType)

    def generateFileName(self) -> str:
        return FileNameGenerator.generateFileName(self.content, self.resolution)

    def setResolution(self, index: int) -> None:
        self.selectedResolutionIndex = index
        self.setFileFormat(self.getAvailableFormat(self.fileFormat))

    @property
    def resolution(self) -> Resolution:
        return self.playback.getResolutions()[self.selectedResolutionIndex]

    def getAvailableFormat(self, currentFormat: str | None = None) -> str:
        defaultFormat = self.optionHistory.getAudioFormat() if self.resolution.isAudioOnly() else self.optionHistory.getFormat()
        availableFormats = self.getAvailableFormats()
        if currentFormat != None:
            if currentFormat in availableFormats:
                return currentFormat
        return defaultFormat if defaultFormat in availableFormats else availableFormats[0]

    def getAvailableFormats(self) -> list[str]:
        if self.resolution.isAudioOnly():
            return self.optionHistory.getAvailableAudioFormats()
        else:
            return self.optionHistory.getAvailableFormats()

    def getPriority(self) -> int:
        return 2 if self.type.isStream() else (1 if self.isPrioritizeEnabled() else 0)

    def setCropRangeMilliseconds(self, startMilliseconds: int | None, endMilliseconds: int | None) -> None:
        self.range = (startMilliseconds, endMilliseconds)

    def setDirectory(self, directory: str) -> None:
        self.directory = directory

    def setAbsoluteFileName(self, absoluteFileName: str) -> None:
        self.directory = os.path.dirname(absoluteFileName)
        self.fileName, self.fileFormat = os.path.basename(absoluteFileName).rsplit(".", 1)

    def setFileName(self, fileName: str) -> None:
        self.fileName = fileName

    def setFileFormat(self, fileFormat: str) -> None:
        self.fileFormat = fileFormat

    def setUnmuteVideoEnabled(self, enabled: bool) -> None:
        self.unmuteVideo = enabled

    def setUpdateTrackEnabled(self, enabled: bool) -> None:
        self.updateTrack = enabled

    def setPrioritizeEnabled(self, enabled: bool) -> None:
        self.prioritize = enabled

    def setSkipAdsEnabled(self, enabled: bool) -> None:
        self.skipAds = enabled

    def setRemuxEnabled(self, enabled: bool) -> None:
        self.remux = enabled

    def isUnmuteVideoEnabled(self) -> bool:
        return self.unmuteVideo

    def isUpdateTrackEnabled(self) -> bool:
        return self.updateTrack

    def isPrioritizeEnabled(self) -> bool:
        return self.prioritize

    def isSkipAdsEnabled(self) -> bool:
        return self.skipAds

    def isRemuxEnabled(self) -> bool:
        return self.remux

    def saveOptionHistory(self) -> None:
        self.optionHistory.setDirectory(self.directory)
        if self.resolution.isAudioOnly():
            self.optionHistory.setAudioFormat(self.fileFormat)
        else:
            self.optionHistory.setFormat(self.fileFormat)
        if self.type.isStream():
            if not self.playback.token.hideAds:
                self.optionHistory.setSkipAdsEnabled(self.skipAds)
            self.optionHistory.setRemuxEnabled(self.remux)
        elif self.type.isVideo():
            self.optionHistory.setUnmuteVideoEnabled(self.unmuteVideo)
            self.optionHistory.setUpdateTrackEnabled(self.updateTrack)
            self.optionHistory.setRemuxEnabled(self.remux)

    def getUrl(self) -> QtCore.QUrl:
        return self.resolution.url

    def getAbsoluteFileName(self) -> str:
        return Utils.joinPath(self.directory, f"{self.fileName}.{self.fileFormat}")