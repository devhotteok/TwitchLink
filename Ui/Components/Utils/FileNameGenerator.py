from Services.Utils.Utils import Utils
from Services.Twitch.Gql import TwitchGqlModels
from Services.Translator.Translator import T
from Database.Database import DB


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
    def generateFileName(cls, videoData, resolution, customTemplate=None):
        if resolution == None:
            resolutionText = T("unknown")
        elif resolution.isAudioOnly():
            resolutionText = T("audio-only")
        else:
            resolutionText = resolution.name
        if isinstance(videoData, TwitchGqlModels.Stream):
            template = cls.getStreamFileNameTemplate()
            variables = cls.getStreamFileNameTemplateVariables(videoData, resolutionText)
        elif isinstance(videoData, TwitchGqlModels.Video):
            template = cls.getVideoFileNameTemplate()
            variables = cls.getVideoFileNameTemplateVariables(videoData, resolutionText)
        else:
            template = cls.getClipFileNameTemplate()
            variables = cls.getClipFileNameTemplateVariables(videoData, resolutionText)
        return Utils.getValidFileName(Utils.injectionSafeFormat(customTemplate or template, **variables))

    @staticmethod
    def getFormData(*args):
        formData = {}
        for data in args:
            formData.update(data)
        return formData

    @staticmethod
    def getInfoTitle(dataType):
        return f"{T(dataType)} {T('#Filename Template Variables')}"

    @staticmethod
    def getBaseInfo(dataType):
        dataType = T(dataType)
        return {
            "{type}": f"{T('file-type')} ({dataType})",
            "{id}": f"{dataType} {T('id')} (XXXXXXXXXX)",
            "{title}": "title",
            "{game}": "category"
        }

    @staticmethod
    def getNameInfo(nameType):
        translated = T(nameType)
        return {
            f"{{{nameType}}}": f"{translated} {T('username')}",
            f"{{{nameType}_name}}": f"{translated} {T('displayname')}",
            f"{{{nameType}_formatted_name}}": T("#'displayname' if {nameType} Displayname is English, otherwise 'displayname(username)'", nameType=translated)
        }

    @staticmethod
    def getTimeInfo(timeType):
        return {
            f"{{{timeType}_at}}": f"{T(f'{timeType}-at')} (YYYY-MM-DD HH:MM:SS)",
            "{date}": f"{T(f'{timeType}-date')} (YYYY-MM-DD)",
            "{year}": f"{T(f'{timeType}-date')} - {T('year')}",
            "{month}": f"{T(f'{timeType}-date')} - {T('month')}",
            "{day}": f"{T(f'{timeType}-date')} - {T('day')}",
            "{time}": f"{T(f'{timeType}-time')} (HH:MM:SS)",
            "{hour}": f"{T(f'{timeType}-time')} - {T('hour')}",
            "{minute}": f"{T(f'{timeType}-time')} - {T('minute')}",
            "{second}": f"{T(f'{timeType}-time')} - {T('second')}"
        }

    @staticmethod
    def getResolutionInfo():
        return {
            "{resolution}": "file-resolution"
        }

    @classmethod
    def getStreamFileNameTemplateFormData(cls):
        return cls.getFormData(
            cls.getBaseInfo("stream"),
            cls.getNameInfo("channel"),
            cls.getTimeInfo("started"),
            cls.getResolutionInfo()
        )

    @classmethod
    def getVideoFileNameTemplateFormData(cls):
        return cls.getFormData(
            cls.getBaseInfo("video"),
            cls.getNameInfo("channel"),
            {
                "{duration}": "duration"
            },
            cls.getTimeInfo("published"),
            {
                "{views}": "views"
            },
            cls.getResolutionInfo()
        )

    @classmethod
    def getClipFileNameTemplateFormData(cls):
        return cls.getFormData(
            cls.getBaseInfo("clip"),
            {
                "{slug}": f"{T('slug')} (SlugExampleHelloTwitch)"
            },
            cls.getNameInfo("channel"),
            cls.getNameInfo("creator"),
            {
                "{duration}": "duration"
            },
            cls.getTimeInfo("created"),
            {
                "{views}": "views"
            },
            cls.getResolutionInfo()
        )