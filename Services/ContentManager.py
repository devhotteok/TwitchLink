from Core import App
from Services.Twitch.GQL import TwitchGQLModels

from PyQt6 import QtCore


class RestrictionType:
    CONTENT_TYPE = 1
    CONTENT_ID = 2


class Exceptions:
    class RestrictedContent(Exception):
        def __init__(self, channel: TwitchGQLModels.User, contentType: str, content: TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip, restrictionType: RestrictionType.CONTENT_TYPE | RestrictionType.CONTENT_ID, reason: str):
            self.channel = channel
            self.contentType = contentType
            self.content = content
            self.restrictionType = restrictionType
            self.reason = reason

        def __str__(self):
            return f"<{self.__class__.__name__} {self.__dict__}>"

        def __repr__(self):
            return self.__str__()


class ContentManager(QtCore.QObject):
    restrictionsUpdated = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.restrictions = {}

    def setRestrictions(self, restrictions: dict) -> None:
        self.restrictions = restrictions
        self.restrictionsUpdated.emit()

    def createPayload(self, content: TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip) -> dict:
        if type(content) == TwitchGQLModels.Stream:
            contentType = "stream"
            channel = content.broadcaster
        elif type(content) == TwitchGQLModels.Video:
            contentType = "video"
            channel = content.owner
        else:
            contentType = "clip"
            channel = content.broadcaster
        return {
            "content": {
                "id": content.id,
                "type": contentType,
                "channel": channel.id
            },
            "user": None if App.Account.user == None else App.Account.user.id
        }

    def createRestrictionData(self, contentId: str, restrictionType: str | None = None, reason: str | None = None) -> dict:
        return {
            "content": contentId,
            "restriction": None if restrictionType == None else {
                "type": restrictionType,
                "reason": reason
            }
        }

    def generateResponse(self, payload: dict) -> dict:
        channelData = self.restrictions.get(payload["content"]["channel"])
        if channelData != None:
            if payload["user"] not in channelData.get("whitelist", []):
                contentTypeData = channelData.get(payload["content"]["type"])
                if contentTypeData != None:
                    if payload["content"]["id"] in contentTypeData:
                        return self.createRestrictionData(
                            contentId=payload["content"]["id"],
                            restrictionType="CONTENT_ID",
                            reason=contentTypeData[payload["content"]["id"]]
                        )
                    elif "*" in contentTypeData:
                        return self.createRestrictionData(
                            contentId=payload["content"]["id"],
                            restrictionType="CONTENT_TYPE",
                            reason=contentTypeData["*"]
                        )
        return self.createRestrictionData(payload["content"]["id"])

    def checkRestriction(self, content: TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip) -> None:
        payload = self.createPayload(content)
        response = self.generateResponse(payload)
        if response["restriction"] != None:
            if type(content) == TwitchGQLModels.Stream:
                contentType = "stream"
                channel = content.broadcaster
            elif type(content) == TwitchGQLModels.Video:
                contentType = "video"
                channel = content.owner
            else:
                contentType = "clip"
                channel = content.broadcaster
            raise Exceptions.RestrictedContent(
                channel,
                contentType,
                content,
                RestrictionType.CONTENT_ID if response["restriction"]["type"] == "CONTENT_ID" else RestrictionType.CONTENT_TYPE,
                response["restriction"]["reason"]
            )

    def checkRestrictions(self, contents: list[TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip]) -> list[Exceptions.RestrictedContent]:
        contentData = {content.id: content for content in contents}
        payload = [self.createPayload(content) for content in contents]
        response = [self.generateResponse(data) for data in payload]
        returnData = []
        for data in response:
            if data["restriction"] != None:
                content = contentData.get(data["content"])
                if type(content) == TwitchGQLModels.Stream:
                    contentType = "stream"
                    channel = content.broadcaster
                elif type(content) == TwitchGQLModels.Video:
                    contentType = "video"
                    channel = content.owner
                else:
                    contentType = "clip"
                    channel = content.broadcaster
                returnData.append(Exceptions.RestrictedContent(
                    channel,
                    contentType,
                    content,
                    RestrictionType.CONTENT_ID if data["restriction"]["type"] == "CONTENT_ID" else RestrictionType.CONTENT_TYPE,
                    data["restriction"]["reason"]
                ))
        return returnData