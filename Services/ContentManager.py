from Core.Config import Config
from Services.Twitch.Gql import TwitchGqlModels
from Services.Translator.Translator import T


class RestrictionType:
    CONTENT_TYPE = 1
    CONTENT_ID = 2


class Restriction:
    def __init__(self, channel, contentType, contentId, restrictionType):
        self.channel = channel
        self.contentType = contentType
        self.contentId = contentId
        self.restrictionType = restrictionType
        self.message = "{}\n\n{}".format(
            T("#'{channel}' has restricted downloading {content}s from their channel." if self.restrictionType == RestrictionType.CONTENT_TYPE else "#'{channel}' has restricted downloading this {content}.", channel=self.channel.displayName, content=T(self.contentType)),
            T("#{appName} respect the rights of streamers.\nTo protect the rights of streamers, {appName} restrict downloads when a content restriction request is received.", appName=Config.APP_NAME)
        )


class _ContentManager:
    def __init__(self):
        self.setRestrictions({})

    def setRestrictions(self, restrictions):
        self.restrictions = restrictions

    def getRestrictions(self, channel, content):
        if type(content) == TwitchGqlModels.Stream:
            contentType = "stream"
        elif type(content) == TwitchGqlModels.Video:
            contentType = "video"
        else:
            contentType = "clip"
        if channel.id in self.restrictions["channel"]:
            if contentType in self.restrictions["channel"][channel.id]:
                return Restriction(channel, contentType, content.id, RestrictionType.CONTENT_TYPE)
        if content.id in self.restrictions[contentType]:
            return Restriction(channel, contentType, content.id, RestrictionType.CONTENT_ID)
        return None

ContentManager = _ContentManager()