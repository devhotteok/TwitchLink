from Services.Utils.Utils import Utils
from Services.Translator.Translator import T
from Database.Database import DB

from os import path


class DownloadInfo:
    class LOG_TEMPLATES:
        STREAM = "[Stream]\nChannel : {channel_formatted_name}\nStarted at : {started_at}\nTitle : {title}\nStream ID : {id}\n{url}"
        VIDEO = "[Video]\nChannel : {channel_formatted_name}\nPublished at : {published_at}\nTitle : {title}\nVideo ID : {id}\n{url}"
        CLIP = "[Clip]\nChannel : {channel_formatted_name}\nCreated at : {created_at}\nTitle : {title}\nClip ID : {slug}\n{url}"

    def __init__(self, videoData, accessToken):
        self.videoData = videoData
        self.accessToken = accessToken
        self.type = self.accessToken.type
        if self.accessToken.type.isStream():
            self.stream = videoData
        elif self.accessToken.type.isVideo():
            self.video = videoData
            self.range = [None, None]
        else:
            self.clip = videoData
        self.resolution = self.accessToken.getResolutions()[0]
        DB.temp.updateDefaultDirectory()
        self.directory = DB.temp.getDefaultDirectory()
        self.fileName = self.createFileName()
        self.fileFormat = self.getDefaultFormatIfAvailable()
        self.saveLog()

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
                "started_at": self.stream.createdAt.toUTC(DB.localization.getTimezone()),
                "date": self.stream.createdAt.date(DB.localization.getTimezone()),
                "time": self.stream.createdAt.time(DB.localization.getTimezone()),
                "resolution": self.getCleanResolutionName()
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
                "published_at": self.video.publishedAt.toUTC(DB.localization.getTimezone()),
                "date": self.video.publishedAt.date(DB.localization.getTimezone()),
                "time": self.video.publishedAt.time(DB.localization.getTimezone()),
                "views": self.video.viewCount,
                "resolution": self.getCleanResolutionName()
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
                "created_at": self.clip.createdAt.toUTC(DB.localization.getTimezone()),
                "date": self.clip.createdAt.date(DB.localization.getTimezone()),
                "time": self.clip.createdAt.time(DB.localization.getTimezone()),
                "views": self.clip.viewCount,
                "resolution": self.getCleanResolutionName()
            }

    def getCleanResolutionName(self):
        resolution = self.resolution
        for key in ["(chunked)", "(source)"]:
            resolution = resolution.replace(key, "")
        return resolution.strip()

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

    def getLogTemplate(self):
        if self.type.isStream():
            return self.LOG_TEMPLATES.STREAM
        elif self.type.isVideo():
            return self.LOG_TEMPLATES.VIDEO
        else:
            return self.LOG_TEMPLATES.CLIP

    def saveLog(self):
        DB.saveLogs(self.getLogTemplate().format(**self.getFileNameTemplateVariables(), url=self.getUrl()))

    def setResolution(self, resolution):
        self.resolution = self.accessToken.getResolutions()[resolution]
        self.fileFormat = self.getDefaultFormatIfAvailable()
        self.saveOptions()

    def getAvailableFormats(self):
        if self.checkAudioOnly():
            return ["aac", "mp3"]
        else:
            if self.type.isClip():
                return ["mp4"]
            else:
                return ["ts", "mp4"]

    def getDefaultFormatIfAvailable(self):
        if DB.temp.getDefaultFormat(self.type.getType()) in self.getAvailableFormats():
            return DB.temp.getDefaultFormat(self.type.getType())
        else:
            return self.getAvailableFormats()[0]

    def checkAudioOnly(self):
        resolution = self.resolution.lower()
        for key in [" ", "-", "_"]:
            resolution = resolution.replace(key, "")
        return "audioonly" in resolution.strip()

    def setCropRange(self, start, end):
        self.range = [start, end]

    def setDirectory(self, directory):
        self.directory = directory

    def setAbsoluteFileName(self, absoluteFileName):
        self.setDirectory(path.dirname(absoluteFileName))
        self.fileName, self.fileFormat = path.basename(absoluteFileName).rsplit(".", 1)
        self.saveOptions()

    def setFileName(self, fileName):
        self.fileName = fileName

    def saveOptions(self):
        DB.temp.setDefaultDirectory(self.directory)
        DB.temp.setDefaultFormat(self.type.getType(), self.fileFormat)

    def getUrl(self):
        return self.accessToken.resolution(self.resolution).url

    def getAbsoluteFileName(self):
        return "{}.{}".format(Utils.joinPath(self.directory, self.fileName), self.fileFormat)