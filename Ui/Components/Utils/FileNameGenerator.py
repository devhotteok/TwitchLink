from Core import App
from Core.App import T
from Services.Utils.Utils import Utils
from Services.Playlist.Resolution import Resolution
from Services.Twitch.GQL import TwitchGQLModels

from PyQt6 import QtCore


class FileNameGenerator:
    @staticmethod
    def combineFormData(*args: dict[str, str]) -> dict[str, str]:
        formData = {}
        for data in args:
            formData.update(data)
        return formData

    @staticmethod
    def getBaseVariables(contentType: str, content: TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip) -> dict[str, str]:
        return {
            "type": T(contentType),
            "id": content.id,
            "title": content.title,
            "game": content.game.displayName
        }

    @staticmethod
    def getUserVariables(name: str, user: TwitchGQLModels.User) -> dict[str, str]:
        return {
            name: user.login,
            f"{name}_name": user.displayName,
            f"{name}_formatted_name": user.formattedName
        }

    @staticmethod
    def getDatetimeVariables(name: str, datetime: QtCore.QDateTime) -> dict[str, str]:
        localDatetime = datetime.toTimeZone(App.Preferences.localization.getTimezone())
        return {
            name: localDatetime.toString("yyyy-MM-dd HH:mm:ss"),
            "date": localDatetime.date().toString("yyyy-MM-dd"),
            "year": f"{localDatetime.date().year():04}",
            "month": f"{localDatetime.date().month():02}",
            "day": f"{localDatetime.date().day():02}",
            "time": localDatetime.time().toString("HH:mm:ss"),
            "hour": f"{localDatetime.time().hour():02}",
            "minute": f"{localDatetime.time().minute():02}",
            "second": f"{localDatetime.time().second():02}"
        }

    @staticmethod
    def getResolutionVariables(resolutionText: str) -> dict[str, str]:
        return {
            "resolution": resolutionText
        }

    @classmethod
    def getStreamFileNameTemplateVariables(cls, stream: TwitchGQLModels.Stream, resolutionText: str) -> dict[str, str]:
        return cls.combineFormData(
            cls.getBaseVariables("stream", stream),
            cls.getUserVariables("channel", stream.broadcaster),
            cls.getDatetimeVariables("started_at", stream.createdAt),
            cls.getResolutionVariables(resolutionText)
        )

    @classmethod
    def getVideoFileNameTemplateVariables(cls, video: TwitchGQLModels.Video, resolutionText: str) -> dict[str, str]:
        return cls.combineFormData(
            cls.getBaseVariables("video", video),
            cls.getUserVariables("channel", video.owner),
            {
                "duration": video.durationString
            },
            cls.getDatetimeVariables("published_at", video.publishedAt),
            {
                "views": str(video.viewCount)
            },
            cls.getResolutionVariables(resolutionText)
        )

    @classmethod
    def getClipFileNameTemplateVariables(cls, clip: TwitchGQLModels.Clip, resolutionText: str) -> dict[str, str]:
        return cls.combineFormData(
            cls.getBaseVariables("clip", clip),
            {
                "slug": clip.slug
            },
            cls.getUserVariables("channel", clip.broadcaster),
            cls.getUserVariables("creator", clip.curator),
            {
                "duration": clip.durationString
            },
            cls.getDatetimeVariables("created_at", clip.createdAt),
            {
                "views": str(clip.viewCount)
            },
            cls.getResolutionVariables(resolutionText)
        )

    @classmethod
    def getStreamFileNameTemplate(cls) -> str:
        return App.Preferences.templates.getStreamFilename()

    @classmethod
    def getVideoFileNameTemplate(cls) -> str:
        return App.Preferences.templates.getVideoFilename()

    @classmethod
    def getClipFileNameTemplate(cls) -> str:
        return App.Preferences.templates.getClipFilename()

    @classmethod
    def generateFileName(cls, content: TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip, resolution: Resolution | None = None, filenameTemplate: str | None = None) -> str:
        resolutionText = T("unknown") if resolution == None else cls.generateResolutionName(resolution)
        if isinstance(content, TwitchGQLModels.Stream):
            defaultFilenameTemplate = cls.getStreamFileNameTemplate()
            variables = cls.getStreamFileNameTemplateVariables(content, resolutionText)
        elif isinstance(content, TwitchGQLModels.Video):
            defaultFilenameTemplate = cls.getVideoFileNameTemplate()
            variables = cls.getVideoFileNameTemplateVariables(content, resolutionText)
        else:
            defaultFilenameTemplate = cls.getClipFileNameTemplate()
            variables = cls.getClipFileNameTemplateVariables(content, resolutionText)
        return Utils.getValidFileName(Utils.injectionSafeFormat(filenameTemplate or defaultFilenameTemplate, **variables))

    @staticmethod
    def generateResolutionName(resolution: Resolution) -> str:
        return T("audio-only") if resolution.isAudioOnly() else f"{resolution.displayName} ({T('source')})" if resolution.isSource() else resolution.displayName

    @staticmethod
    def getInfoTitle(contentType: str) -> str:
        return f"{T(contentType)} {T('#Filename Template Variables')}"

    @staticmethod
    def getBaseInfo(contentType: str) -> dict[str, str]:
        contentType = T(contentType)
        return {
            "{type}": f"{T('file-type')} ({contentType})",
            "{id}": f"{contentType} {T('id')} (XXXXXXXXXX)",
            "{title}": "title",
            "{game}": "category"
        }

    @staticmethod
    def getNameInfo(nameType: str) -> dict[str, str]:
        translated = T(nameType)
        return {
            f"{{{nameType}}}": f"{translated} {T('username')}",
            f"{{{nameType}_name}}": f"{translated} {T('displayname')}",
            f"{{{nameType}_formatted_name}}": T("#'displayname' if {nameType} Displayname is English, otherwise 'displayname(username)'", nameType=translated)
        }

    @staticmethod
    def getTimeInfo(timeType: str) -> dict[str, str]:
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
    def getResolutionInfo() -> dict[str, str]:
        return {
            "{resolution}": "file-resolution"
        }

    @classmethod
    def getStreamFileNameTemplateFormData(cls) -> dict[str, str]:
        return cls.combineFormData(
            cls.getBaseInfo("stream"),
            cls.getNameInfo("channel"),
            cls.getTimeInfo("started"),
            cls.getResolutionInfo()
        )

    @classmethod
    def getVideoFileNameTemplateFormData(cls) -> dict[str, str]:
        return cls.combineFormData(
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
    def getClipFileNameTemplateFormData(cls) -> dict[str, str]:
        return cls.combineFormData(
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