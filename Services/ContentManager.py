from Services.Twitch.Gql import TwitchGqlModels

from PyQt6 import QtCore


class RestrictionType:
    CONTENT_TYPE = 1
    CONTENT_ID = 2


class Exceptions:
    class RestrictedContent(Exception):
        def __init__(self, channel, contentType, content, reason, restrictionType):
            self.channel = channel
            self.contentType = contentType
            self.content = content
            self.reason = reason
            self.restrictionType = restrictionType

        def __str__(self):
            return f"<{self.__class__.__name__} {self.__dict__}>"

        def __repr__(self):
            return self.__str__()


class _ContentManager(QtCore.QObject):
    restrictionsUpdated = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(_ContentManager, self).__init__(parent=parent)
        self.restrictions = {}

    def setRestrictions(self, restrictions):
        self.restrictions = restrictions
        self.restrictionsUpdated.emit()

    def checkRestrictions(self, content, user=None, fetch=False):
        if type(content) == TwitchGqlModels.Stream:
            contentType = "stream"
            channel = content.broadcaster
        elif type(content) == TwitchGqlModels.Video:
            contentType = "video"
            channel = content.owner
        else:
            contentType = "clip"
            channel = content.broadcaster
        channelData = self.restrictions.get(str(channel.id))
        if channelData == None:
            return
        if user != None:
            if str(user.id) in channelData.get("whitelist", []):
                return
        contentTypeData = channelData.get(contentType)
        if contentTypeData == None:
            return
        if str(content.id) in contentTypeData:
            raise Exceptions.RestrictedContent(
                channel,
                contentType,
                content,
                contentTypeData[str(content.id)],
                RestrictionType.CONTENT_ID
            )
        elif "*" in contentTypeData:
            raise Exceptions.RestrictedContent(
                channel,
                contentType,
                content,
                contentTypeData["*"],
                RestrictionType.CONTENT_TYPE
            )

ContentManager = _ContentManager()