from Database.Database import DB
from Services.Utils.Utils import Utils
from Services.Twitch.Gql import TwitchGqlModels
from Services.Translator.Translator import T


class FileNameGenerator:
    @classmethod
    def combineTemplateVariables(cls, *args):
        formData = {}
        for data in args:
            formData.update(data)
        return formData

    @classmethod
    def getBaseVariables(cls, dataType, videoData):
        return {
            "type": T(dataType),
            "id": videoData.id,
            "title": videoData.title,
            "game": videoData.game.displayName
        }

    @classmethod
    def getChannelVariables(cls, name, channel):
        return {
            name: channel.login,
            f"{name}_name": channel.displayName,
            f"{name}_formatted_name": channel.formattedName
        }

    @classmethod
    def getDatetimeVariables(cls, name, datetime):
        return {
            name: datetime.toString("yyyy-MM-dd HH:mm:ss"),
            "date": datetime.date().toString("yyyy-MM-dd"),
            "year": f"{datetime.date().year():04}",
            "month": f"{datetime.date().month():02}",
            "day": f"{datetime.date().day():02}",
            "time": datetime.time().toString("HH:mm:ss"),
            "hour": f"{datetime.time().hour():02}",
            "minute": f"{datetime.time().minute():02}",
            "second": f"{datetime.time().second():02}"
        }

    @classmethod
    def getResolutionVariables(self, resolutionText):
        return {
            "resolution": resolutionText
        }

    @classmethod
    def getStreamFileNameTemplateVariables(cls, stream, resolutionText):
        startedAt = stream.createdAt.toTimeZone(DB.localization.getTimezone())
        return cls.combineTemplateVariables(
            cls.getBaseVariables("stream", stream),
            cls.getChannelVariables("channel", stream.broadcaster),
            cls.getDatetimeVariables("started_at", startedAt),
            cls.getResolutionVariables(resolutionText)
        )

    @classmethod
    def getVideoFileNameTemplateVariables(cls, video, resolutionText):
        publishedAt = video.publishedAt.toTimeZone(DB.localization.getTimezone())
        return cls.combineTemplateVariables(
            cls.getBaseVariables("video", video),
            cls.getChannelVariables("channel", video.owner),
            {
                "duration": video.durationString
            },
            cls.getDatetimeVariables("published_at", publishedAt),
            {
                "views": video.viewCount
            },
            cls.getResolutionVariables(resolutionText)
        )

    @classmethod
    def getClipFileNameTemplateVariables(cls, clip, resolutionText):
        createdAt = clip.createdAt.toTimeZone(DB.localization.getTimezone())
        return cls.combineTemplateVariables(
            cls.getBaseVariables("clip", clip),
            {
                "slug": clip.slug
            },
            cls.getChannelVariables("channel", clip.broadcaster),
            cls.getChannelVariables("creator", clip.curator),
            {
                "duration": clip.durationString
            },
            cls.getDatetimeVariables("created_at", createdAt),
            {
                "views": clip.viewCount
            },
            cls.getResolutionVariables(resolutionText)
        )

    @classmethod
    def getStreamFileNameTemplate(cls):
        return DB.templates.getStreamFilename()

    @classmethod
    def getVideoFileNameTemplate(cls):
        return DB.templates.getVideoFilename()

    @classmethod
    def getClipFileNameTemplate(cls):
        return DB.templates.getClipFilename()

    @classmethod
    def generateFileName(cls, videoData, resolutionText):
        if isinstance(videoData, TwitchGqlModels.Stream):
            template = cls.getStreamFileNameTemplate()
            variables = cls.getStreamFileNameTemplateVariables(videoData, resolutionText)
        elif isinstance(videoData, TwitchGqlModels.Video):
            template = cls.getVideoFileNameTemplate()
            variables = cls.getVideoFileNameTemplateVariables(videoData, resolutionText)
        else:
            template = cls.getClipFileNameTemplate()
            variables = cls.getClipFileNameTemplateVariables(videoData, resolutionText)
        return Utils.getValidFileName(Utils.injectionSafeFormat(template, **variables))