from Services.Utils.Utils import Utils
from Services.Translator.Translator import T
from Database.Database import DB

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
            startedAt = self.stream.createdAt.asTimezone(DB.localization.getTimezone())
            return {
                "type": T(self.type.toString()),
                "id": self.stream.id,
                "title": self.stream.title,
                "game": self.stream.game.displayName,
                "channel": self.stream.broadcaster.login,
                "channel_name": self.stream.broadcaster.displayName,
                "channel_formatted_name": self.stream.broadcaster.formattedName(),
                "started_at": startedAt,
                "date": startedAt.date(),
                "year": f"{startedAt.year:04}",
                "month": f"{startedAt.month:02}",
                "day": f"{startedAt.day:02}",
                "time": startedAt.time(),
                "hour": f"{startedAt.hour:02}",
                "minute": f"{startedAt.minute:02}",
                "second": f"{startedAt.second:02}",
                "resolution": self.resolution.resolutionName
            }
        elif self.type.isVideo():
            publishedAt = self.video.publishedAt.asTimezone(DB.localization.getTimezone())
            return {
                "type": T(self.type.toString()),
                "id": self.video.id,
                "title": self.video.title,
                "game": self.video.game.displayName,
                "channel": self.video.owner.login,
                "channel_name": self.video.owner.displayName,
                "channel_formatted_name": self.video.owner.formattedName(),
                "duration": self.video.lengthSeconds,
                "published_at": publishedAt,
                "date": publishedAt.date(),
                "year": f"{publishedAt.year:04}",
                "month": f"{publishedAt.month:02}",
                "day": f"{publishedAt.day:02}",
                "time": publishedAt.time(),
                "hour": f"{publishedAt.hour:02}",
                "minute": f"{publishedAt.minute:02}",
                "second": f"{publishedAt.second:02}",
                "views": self.video.viewCount,
                "resolution": self.resolution.resolutionName
            }
        else:
            createdAt = self.clip.createdAt.asTimezone(DB.localization.getTimezone())
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
                "created_at": createdAt,
                "date": createdAt.date(),
                "year": f"{createdAt.year:04}",
                "month": f"{createdAt.month:02}",
                "day": f"{createdAt.day:02}",
                "time": createdAt.time(),
                "hour": f"{createdAt.hour:02}",
                "minute": f"{createdAt.minute:02}",
                "second": f"{createdAt.second:02}",
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