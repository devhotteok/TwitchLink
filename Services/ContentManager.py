from Core.Config import Config
from Services.Twitch.Gql import TwitchGqlModels
from Services.Translator.Translator import Translator, T


class RestrictionType:
    CONTENT_TYPE = 1
    CONTENT_ID = 2


class Restriction:
    def __init__(self, channel, contentType, contentId, reason, restrictionType):
        self.channel = channel
        self.contentType = contentType
        self.contentId = contentId
        self.reason = reason.get(Translator.getLanguage())
        self.restrictionType = restrictionType
        self.message = "{}\n\n{}".format(
            T("#{content} downloads for this channel have been restricted either by the streamer({channel})'s request or by the administrator." if self.restrictionType == RestrictionType.CONTENT_TYPE else "#This content has been restricted by the request of the streamer({channel}) or by the administrator.", channel=self.channel.displayName, content=T(self.contentType)),
            T("#To protect the rights of streamers, {appName} restrict downloads when a content restriction request is received.", appName=Config.APP_NAME)
        )
        if self.reason != None:
            self.message = f"{self.message}\n\n[{T('reason')}]\n{self.reason}"


class ContentManager:
    restrictions = {}

    @classmethod
    def setRestrictions(cls, restrictions):
        cls.restrictions = restrictions

    @classmethod
    def getRestrictions(cls, channel, content):
        if type(content) == TwitchGqlModels.Stream:
            contentType = "stream"
        elif type(content) == TwitchGqlModels.Video:
            contentType = "video"
        else:
            contentType = "clip"
        if channel.id in cls.restrictions["channel"]:
            if contentType in cls.restrictions["channel"][channel.id]:
                return Restriction(channel, contentType, content.id, cls.restrictions["channel"][channel.id][contentType], RestrictionType.CONTENT_TYPE)
        if content.id in cls.restrictions[contentType]:
            return Restriction(channel, contentType, content.id, cls.restrictions[contentType][content.id], RestrictionType.CONTENT_ID)
        return None