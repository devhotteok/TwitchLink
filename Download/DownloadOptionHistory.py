from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Database.EncoderDecoder import Codable

import os


class FileHistory:
    SUPPORTED_FORMATS = [
        ""
    ]

    def __init__(self):
        super(FileHistory, self).__init__()
        self.setDirectory(Config.DEFAULT_DIRECTORY)
        self.setFormat(self.getAvailableFormats()[0])

    def setAbsoluteFileName(self, absoluteFileName):
        self.setDirectory(os.path.dirname(absoluteFileName))
        self.setFormat(os.path.basename(absoluteFileName).rsplit(".", 1)[1])

    def setDirectory(self, directoryHistory):
        self._directory = directoryHistory

    def setFormat(self, formatHistory):
        self._format = formatHistory

    def getDirectory(self):
        return self._directory

    def getUpdatedDirectory(self):
        for directory in [self.getDirectory(), Config.DEFAULT_DIRECTORY, Config.APPDATA_PATH]:
            try:
                OSUtils.createDirectory(directory)
                return directory
            except:
                pass
        return self.getDirectory()

    def getFormat(self):
        return self._format

    def getAvailableFormats(self):
        return self.SUPPORTED_FORMATS


class AudioFormatHistory:
    SUPPORTED_AUDIO_FORMATS = [
        "aac",
        "mp3"
    ]

    def __init__(self):
        super(AudioFormatHistory, self).__init__()
        self.setAudioFormat(self.getAvailableAudioFormats()[0])

    def setAudioFormat(self, audioFormat):
        self._audioFormat = audioFormat

    def getAudioFormat(self):
        return self._audioFormat

    def getAvailableAudioFormats(self):
        return self.SUPPORTED_AUDIO_FORMATS


class OptimizeFileHistory:
    def __init__(self):
        super(OptimizeFileHistory, self).__init__()
        self.setOptimizeFileEnabled(False)

    def setOptimizeFileEnabled(self, optimizeFile):
        self._optimizeFile = optimizeFile

    def isOptimizeFileEnabled(self):
        return self._optimizeFile


class StreamHistory(FileHistory, AudioFormatHistory, OptimizeFileHistory, Codable):
    SUPPORTED_FORMATS = [
        "ts",
        "mp4"
    ]


class VideoHistory(FileHistory, AudioFormatHistory, OptimizeFileHistory, Codable):
    SUPPORTED_FORMATS = [
        "ts",
        "mp4"
    ]

    def __init__(self):
        super(VideoHistory, self).__init__()
        self.setUnmuteVideoEnabled(False)
        self.setUpdateTrackEnabled(False)

    def setUnmuteVideoEnabled(self, unmuteVideo):
        self._unmuteVideo = unmuteVideo

    def setUpdateTrackEnabled(self, updateTrack):
        self._updateTrack = updateTrack

    def isUnmuteVideoEnabled(self):
        return self._unmuteVideo

    def isUpdateTrackEnabled(self):
        return self._updateTrack


class ClipHistory(FileHistory, Codable):
    SUPPORTED_FORMATS = [
        "mp4"
    ]


class ThumbnailHistory(FileHistory, Codable):
    SUPPORTED_FORMATS = [
        "jpg",
        "png"
    ]