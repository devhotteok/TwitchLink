from Database.EncoderDecoder import Codable

from PyQt5 import QtCore


class DataUtils:
    @staticmethod
    def getId(string):
        return None if string == None else int(string)

    @staticmethod
    def cleanString(string):
        return string.replace("\n", "").replace("\r", "")


class TimeUtils:
    DEFAULT_DATETIME = "0001-01-01T00:00:00Z"

    @classmethod
    def Datetime(cls, string):
        try:
            datetime = QtCore.QDateTime.fromString(string or cls.DEFAULT_DATETIME, QtCore.Qt.ISODateWithMs)
            datetime.setTimeSpec(QtCore.Qt.UTC)
            return datetime
        except:
            return QtCore.QDateTime.fromString(cls.DEFAULT_DATETIME, QtCore.Qt.ISODateWithMs)


class TwitchGqlObject(Codable):
    @classmethod
    def __model__(cls, data):
        return cls({})

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class User(TwitchGqlObject):
    def __init__(self, data):
        self.id = DataUtils.getId(data.get("id"))
        self.login = data.get("login") or ""
        self.displayName = data.get("displayName", self.login)
        self.profileImageURL = data.get("profileImageURL") or ""
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))

    @property
    def formattedName(self):
        if self.displayName.lower() == self.login.lower():
            return self.displayName
        else:
            return f"{self.displayName}({self.login})"

class Channel(User):
    def __init__(self, data):
        super(Channel, self).__init__(data)
        self.description = data.get("description") or ""
        self.primaryColorHex = data.get("primaryColorHex") or ""
        self.offlineImageURL = data.get("offlineImageURL") or ""
        self.profileURL = data.get("profileURL") or ""
        self.isPartner = data.get("roles", {}).get("isPartner", False)
        self.isAffiliate = data.get("roles", {}).get("isAffiliate", False)
        self.isStaff = data.get("roles", {}).get("isStaff", False)
        self.followers = data.get("followers", {}).get("totalCount", 0)
        self.lastBroadcast = Broadcast(data.get("lastBroadcast") or {})
        self.stream = None if data.get("stream") == None else Stream(data.get("stream"))

    @property
    def isVerified(self):
        return self.isPartner

class Broadcast(TwitchGqlObject):
    def __init__(self, data):
        self.id = DataUtils.getId(data.get("id"))
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.startedAt = TimeUtils.Datetime(data.get("startedAt"))

class Stream(TwitchGqlObject):
    def __init__(self, data):
        self.id = DataUtils.getId(data.get("id"))
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.type = data.get("type") or ""
        self.previewImageURL = data.get("previewImageURL") or ""
        self.broadcaster = User(data.get("broadcaster") or {})
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.viewersCount = data.get("viewersCount", 0)

    def isLive(self):
        return self.type == "live"

    def isRerun(self):
        return self.type == "rerun"

class Video(TwitchGqlObject):
    def __init__(self, data):
        self.id = DataUtils.getId(data.get("id"))
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.previewThumbnailURL = data.get("previewThumbnailURL") or ""
        self.owner = User(data.get("owner") or {})
        self.creator = User(data.get("creator") or {})
        self.lengthSeconds = float(data.get("lengthSeconds", 0))
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.publishedAt = TimeUtils.Datetime(data.get("publishedAt"))
        self.viewCount = data.get("viewCount", 0)

    @property
    def durationString(self):
        seconds = int(self.lengthSeconds)
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 3600 % 60:02}"

class Clip(TwitchGqlObject):
    def __init__(self, data):
        self.id = DataUtils.getId(data.get("id"))
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.thumbnailURL = data.get("thumbnailURL") or ""
        self.slug = data.get("slug") or ""
        self.url = data.get("url") or ""
        self.broadcaster = User(data.get("broadcaster") or {})
        self.curator = User(data.get("curator") or {})
        self.durationSeconds = float(data.get("durationSeconds", 0))
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.viewCount = data.get("viewCount", 0)

    @property
    def durationString(self):
        seconds = int(self.durationSeconds)
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 3600 % 60:02}"

class Game(TwitchGqlObject):
    def __init__(self, data):
        self.id = DataUtils.getId(data.get("id"))
        self.name = data.get("name") or ""
        self.boxArtURL = data.get("boxArtURL") or ""
        self.displayName = data.get("displayName", self.name)