from Services.Utils.Utils import Utils
from Services.Translator.Translator import T
from Database.Database import DB

import datetime

import os


class DownloadInfo:
    def __init__(self, videoData, accessToken):
        self.videoData = videoData
        self.accessToken = accessToken
        self.type = self.accessToken.type
        self.history = DB.temp.getDownloadHistory(self.type.getType())
        if self.accessToken.type.isStream():
            self.stream = videoData
        elif self.accessToken.type.isVideo():
            self.video = videoData
            self.range = [None, None]
            self.unmuteVideo = self.history.isUnmuteVideoEnabled()
            self.updateTrack = self.history.isUpdateTrackEnabled()
            self.prioritize = False
        else:
            self.clip = videoData
            self.prioritize = False
        self.resolution = self.accessToken.getResolutions()[0]
        self.directory = self.history.getUpdatedDirectory()
        self.fileName = self.createFileName()
        self.fileFormat = self.getAvailableFormat()

    def getFileNameTemplateVariables(self):
        if self.type.isStream():
            return {
                "type": T(self.type.toString()),
                "id": self.stream.id,
                "title": self.stream.title,
                "game": self.stream.game.displayName,
                "channel": self.stream.broadcaster.login,
                "channel_name": self.stream.broadcaster.displayName,
                "channel_formatted_name": self.stream.broadcaster.formattedName(),
                "started_at": self.stream.createdAt.asTimezone(DB.localization.getTimezone()),
                "date": self.stream.createdAt.date(DB.localization.getTimezone()),
                "time": self.stream.createdAt.time(DB.localization.getTimezone()),
                "resolution": self.resolution.resolutionName
            }
        elif self.type.isVideo():
            return {
                "type": T(self.type.toString()),
                "id": self.video.id,
                "title": self.video.title,
                "game": self.video.game.displayName,
                "channel": self.video.owner.login,
                "channel_name": self.video.owner.displayName,
                "channel_formatted_name": self.video.owner.formattedName(),
                "duration": self.video.lengthSeconds,
                "published_at": self.video.publishedAt.asTimezone(DB.localization.getTimezone()),
                "date": self.video.publishedAt.date(DB.localization.getTimezone()),
                "time": self.video.publishedAt.time(DB.localization.getTimezone()),
                "views": self.video.viewCount,
                "resolution": self.resolution.resolutionName
            }
        else:
            return {
                "type": T(self.type.toString()),
                "id": self.clip.id,
                "title": self.clip.title,
                "game": self.clip.game.displayName,
                "slug": self.clip.slug,
                "channel": self.clip.broadcaster.login,
                "channel_name": self.clip.broadcaster.displayName,
                "channel_formatted_name": self.clip.broadcaster.formattedName(),
                "creator": self.clip.curator.login,
                "creator_name": self.clip.curator.displayName,
                "creator_formatted_name": self.clip.curator.formattedName(),
                "duration": self.clip.durationSeconds,
                "created_at": self.clip.createdAt.asTimezone(DB.localization.getTimezone()),
                "date": self.clip.createdAt.date(DB.localization.getTimezone()),
                "time": self.clip.createdAt.time(DB.localization.getTimezone()),
                "views": self.clip.viewCount,
                "resolution": self.resolution.resolutionName
            }

    def getFileNameTemplate(self):
        if self.type.isStream():
            return DB.templates.getStreamFilename()
        elif self.type.isVideo():
            return DB.templates.getVideoFilename()
        else:
            return DB.templates.getClipFilename()

    def createFileName(self):
        return Utils.getValidFileName(Utils.injectionSafeFormat(self.getFileNameTemplate(), **self.getFileNameTemplateVariables()))

    def checkResolutionInFileName(self):
        return "{resolution}" in self.getFileNameTemplate()

    def getObjectData(self, object):
        if hasattr(object, "__dict__"):
            return self.getObjectData(object.__dict__)
        elif isinstance(object, dict):
            data = {}
            for key in object:
                data[key] = self.getObjectData(object[key])
            return data
        elif isinstance(object, list):
            data = []
            for value in object:
                data.append(self.getObjectData(value))
            return data
        elif isinstance(object, datetime.datetime) or isinstance(object, datetime.timedelta):
            return self.getObjectData(str(object))
        else:
            return object

    def setResolution(self, resolution):
        self.resolution = resolution
        self.fileFormat = self.getAvailableFormat()

    def getAvailableFormat(self):
        defaultFormat = self.history.getAudioFormat() if self.resolution.isAudioOnly() else self.history.getFormat()
        availableFormats = self.getAvailableFormats()
        return defaultFormat if defaultFormat in availableFormats else availableFormats[0]

    def getAvailableFormats(self):
        if self.resolution.isAudioOnly():
            return self.history.getAvailableAudioFormats()
        else:
            return self.history.getAvailableFormats()

    def setCropRange(self, start, end):
        self.range = [start, end]

    def setDirectory(self, directory):
        self.directory = directory

    def setAbsoluteFileName(self, absoluteFileName):
        self.setDirectory(os.path.dirname(absoluteFileName))
        self.fileName, self.fileFormat = os.path.basename(absoluteFileName).rsplit(".", 1)

    def setFileName(self, fileName):
        self.fileName = fileName

    def setFileFormat(self, fileFormat):
        self.fileFormat = fileFormat

    def setUnmuteVideoEnabled(self, unmuteVideo):
        self.unmuteVideo = unmuteVideo

    def setUpdateTrackEnabled(self, updateTrack):
        self.updateTrack = updateTrack

    def setPrioritizeEnabled(self, prioritize):
        self.prioritize = prioritize

    def isUnmuteVideoEnabled(self):
        return self.unmuteVideo

    def isUpdateTrackEnabled(self):
        return self.updateTrack

    def isPrioritizeEnabled(self):
        return self.prioritize

    def saveHistory(self):
        self.history.setDirectory(self.directory)
        if self.resolution.isAudioOnly():
            self.history.setAudioFormat(self.fileFormat)
        else:
            self.history.setFormat(self.fileFormat)
        if self.accessToken.type.isVideo():
            self.history.setUnmuteVideoEnabled(self.unmuteVideo)
            self.history.setUpdateTrackEnabled(self.updateTrack)

    def getUrl(self):
        return self.resolution.url

    def getAbsoluteFileName(self):
        return f"{Utils.joinPath(self.directory, self.fileName)}.{self.fileFormat}"