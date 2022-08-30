from Services.Twitch.Gql import TwitchGqlModels
from Services.Translator.Translator import Translator, T


class RestrictionType:
    CONTENT_TYPE = 1
    CONTENT_ID = 2


class Exceptions:
    class RestrictedContent(Exception):
        def __init__(self, channel, contentType, contentId, reason, restrictionType):
            self.channel = channel
            self.contentType = contentType
            self.contentId = contentId
            self.reason = reason.get(Translator.getLanguage())
            self.restrictionType = restrictionType

        def __str__(self):
            return f"<{self.__class__.__name__} {self.__dict__}>"

        def __repr__(self):
            return self.__str__()


class ContentManager:
    restrictions = {}

    @classmethod
    def setRestrictions(cls, restrictions):
        cls.restrictions = restrictions

    @classmethod
    def checkRestrictions(cls, channel, content):
        if type(content) == TwitchGqlModels.Stream:
            contentType = "stream"
        elif type(content) == TwitchGqlModels.Video:
            contentType = "video"
        else:
            contentType = "clip"
        if channel.id in cls.restrictions["channel"]:
            if contentType in cls.restrictions["channel"][channel.id]:
                raise Exceptions.RestrictedContent(channel, contentType, content.id, cls.restrictions["channel"][channel.id][contentType], RestrictionType.CONTENT_TYPE)
        if content.id in cls.restrictions[contentType]:
            raise Exceptions.RestrictedContent(channel, contentType, content.id, cls.restrictions[contentType][content.id], RestrictionType.CONTENT_ID)