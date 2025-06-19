from AppData.EncoderDecoder import Serializable

from PyQt6 import QtCore

import json


class DataUtils:
    @staticmethod
    def cleanString(string: str) -> str:
        return string.replace("\n", "").replace("\r", "")


class TimeUtils:
    DEFAULT_DATETIME = "0001-01-01T00:00:00Z"

    @classmethod
    def Datetime(cls, string: str) -> QtCore.QDateTime:
        datetime = QtCore.QDateTime.fromString(string or cls.DEFAULT_DATETIME, QtCore.Qt.DateFormat.ISODateWithMs)
        if not datetime.isValid():
            datetime = QtCore.QDateTime.fromString(cls.DEFAULT_DATETIME, QtCore.Qt.DateFormat.ISODateWithMs)
        datetime.setTimeSpec(QtCore.Qt.TimeSpec.UTC)
        return datetime


class TwitchGQLObject(Serializable):
    @classmethod
    def __model__(cls, data):
        return cls({})

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class User(TwitchGQLObject):
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.login: str = data.get("login") or ""
        self.displayName: str = data.get("displayName", self.login)
        self.profileImageURL: str = data.get("profileImageURL") or ""
        self.createdAt: QtCore.QDateTime = TimeUtils.Datetime(data.get("createdAt"))

    @property
    def formattedName(self) -> str:
        if self.displayName.lower() == self.login.lower():
            return self.displayName
        else:
            return f"{self.displayName}({self.login})"

class Channel(User):
    def __init__(self, data: dict):
        super().__init__(data)
        self.description: str = data.get("description") or ""
        self.primaryColorHex: str = data.get("primaryColorHex") or ""
        self.offlineImageURL: str = data.get("offlineImageURL") or ""
        self.profileURL: str = data.get("profileURL") or ""
        self.isPartner: bool = data.get("roles", {}).get("isPartner", False)
        self.isAffiliate: bool = data.get("roles", {}).get("isAffiliate", False)
        self.isStaff: bool = data.get("roles", {}).get("isStaff", False)
        self.followers: int = data.get("followers", {}).get("totalCount", 0)
        self.lastBroadcast: Broadcast = Broadcast(data.get("lastBroadcast") or {})
        self.stream: Stream | None = None if data.get("stream") == None else Stream(data.get("stream"))

    @property
    def isVerified(self) -> bool:
        return self.isPartner

    def getUser(self) -> User:
        user = User({})
        for key in user.__dict__.keys():
            setattr(user, key, getattr(self, key))
        return user

class Broadcast(TwitchGQLObject):
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.title: str = DataUtils.cleanString(data.get("title") or "")
        self.game: Game = Game(data.get("game") or {})
        self.startedAt: QtCore.QDateTime = TimeUtils.Datetime(data.get("startedAt"))

class Stream(TwitchGQLObject):
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.title: str = DataUtils.cleanString(data.get("title") or "")
        self.game: Game = Game(data.get("game") or {})
        self.type: str = data.get("type") or ""
        self.previewImageURL: str = data.get("previewImageURL") or ""
        self.broadcaster: User = User(data.get("broadcaster") or {})
        self.createdAt: QtCore.QDateTime = TimeUtils.Datetime(data.get("createdAt"))
        self.viewersCount: int = data.get("viewersCount", 0)

    def isLive(self) -> bool:
        return not self.isRerun()

    def isRerun(self) -> bool:
        return self.type == "rerun"

class Video(TwitchGQLObject):
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.title: str = DataUtils.cleanString(data.get("title") or "")
        self.game: Game = Game(data.get("game") or {})
        self.previewThumbnailURL: str = data.get("previewThumbnailURL") or ""
        self.owner: User = User(data.get("owner") or {})
        self.creator: User = User(data.get("creator") or {})
        self.lengthSeconds: float = float(data.get("lengthSeconds", 0))
        self.createdAt: QtCore.QDateTime = TimeUtils.Datetime(data.get("createdAt"))
        self.publishedAt: QtCore.QDateTime = TimeUtils.Datetime(data.get("publishedAt"))
        self.viewCount: int = data.get("viewCount", 0)

    @property
    def durationString(self) -> str:
        seconds = int(self.lengthSeconds)
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 3600 % 60:02}"

class Clip(TwitchGQLObject):
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.title: str = DataUtils.cleanString(data.get("title") or "")
        self.game: Game = Game(data.get("game") or {})
        self.thumbnailURL: str = data.get("thumbnailURL") or ""
        self.slug: str = data.get("slug") or ""
        self.url: str = data.get("url") or ""
        self.broadcaster: User = User(data.get("broadcaster") or {})
        self.curator: User = User(data.get("curator") or {})
        self.durationSeconds: float = float(data.get("durationSeconds", 0))
        self.createdAt: QtCore.QDateTime = TimeUtils.Datetime(data.get("createdAt"))
        self.viewCount: int = data.get("viewCount", 0)

    @property
    def durationString(self) -> str:
        seconds = int(self.durationSeconds)
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 3600 % 60:02}"

class Game(TwitchGQLObject):
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.name: str = data.get("name") or ""
        self.boxArtURL: str = data.get("boxArtURL") or ""
        self.displayName: str = data.get("displayName", self.name)

class StreamPlaybackAccessToken(TwitchGQLObject):
    def __init__(self, data: dict, streamAdRequestHandling: dict | None = None):
        self.signature: str = data.get("signature") or ""
        self.value: str = data.get("value") or ""
        self.streamAdRequestHandling = streamAdRequestHandling or {}

    @property
    def tokenData(self) -> dict:
        try:
            return json.loads(self.value)
        except:
            return {}

    @property
    def hideAds(self) -> bool:
        try:
            hasTurbo = self.streamAdRequestHandling["currentUser"]["hasTurbo"]
            subscriptionBenefit = self.streamAdRequestHandling["user"]["self"]["subscriptionBenefit"]
            adProperties = self.streamAdRequestHandling["user"]["adProperties"]
            if hasTurbo:
                return True
            if subscriptionBenefit != None and subscriptionBenefit["product"]["hasAdFree"]:
                return True
            if adProperties["hasPrerollsDisabled"] and adProperties["hasPostrollsDisabled"]:
                return True
        except:
            pass
        return False

    @property
    def forbidden(self) -> bool:
        return True if self.tokenData.get("authorization", {}).get("forbidden") else False

    def getForbiddenReason(self) -> str | None:
        return self.tokenData.get("authorization", {}).get("reason") if self.forbidden else None

    @property
    def geoBlock(self) -> bool:
        return True if self.tokenData.get("ci_gb") else False

    def getGeoBlockReason(self) -> str | None:
        return self.tokenData.get("geoblock_reason") if self.geoBlock else None

class VideoPlaybackAccessToken(TwitchGQLObject):
    def __init__(self, data: dict):
        self.signature: str = data.get("signature") or ""
        self.value: str = data.get("value") or ""

class ClipPlaybackAccessToken(TwitchGQLObject):
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.videoQualities: list[dict] = data.get("videoQualities")
        self.signature: str = data.get("playbackAccessToken", {}).get("signature") or ""
        self.value: str = data.get("playbackAccessToken", {}).get("value") or ""