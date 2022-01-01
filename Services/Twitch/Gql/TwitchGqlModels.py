from datetime import datetime, timedelta


class Utils:
    @staticmethod
    def getObject(model, data):
        return None if data == None else model(data)

    @staticmethod
    def cleanString(string):
        return string.replace("\n", "").replace("\r", "")

class TimeUtils:
    class Datetime:
        DEFAULT_DATETIME = "0001-01-01T00:00:00Z"

        def __init__(self, string):
            if string == None:
                string = self.DEFAULT_DATETIME
            try:
                self.datetime = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                try:
                    self.datetime = datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")
                except:
                    self.datetime = datetime.strptime(self.DEFAULT_DATETIME, "%Y-%m-%dT%H:%M:%SZ")

        def __str__(self):
            return self.datetime.__str__()

        def __repr__(self):
            return self.__str__()

        def toUTC(self, UTC=None):
            if UTC == None:
                return self.datetime
            else:
                try:
                    return self.datetime + timedelta(seconds=UTC.total_seconds())
                except:
                    return self.datetime

        def date(self, UTC=None):
            return self.toUTC(UTC).date()

        def time(self, UTC=None):
            return self.toUTC(UTC).time()

    class Duration:
        def __init__(self, seconds):
            self.timedelta = timedelta(seconds=seconds)

        def totalSeconds(self):
            return int(self.timedelta.total_seconds())

        def __str__(self):
            seconds = self.totalSeconds()
            return "{:02}:{:02}:{:02}".format(seconds // 3600, seconds % 3600 // 60, seconds % 3600 % 60)

        def __repr__(self):
            return self.__str__()

class User:
    def __init__(self, data):
        self.id = data.get("id")
        self.login = data.get("login") or ""
        self.displayName = data.get("displayName", self.login)
        self.profileImageURL = data.get("profileImageURL") or ""
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))

    def formattedName(self):
        if self.id == None:
            return "Unknown User"
        if self.displayName.lower() == self.login:
            return self.displayName
        else:
            return "{}({})".format(self.displayName, self.login)

    def __str__(self):
        return "<User {}>".format(self.__dict__)

    def __repr__(self):
        return self.__str__()

class Channel(User):
    def __init__(self, data):
        super().__init__(data)
        self.description = data.get("description") or ""
        self.primaryColorHex = data.get("primaryColorHex") or ""
        self.offlineImageURL = data.get("offlineImageURL") or ""
        self.isPartner = data.get("roles", {}).get("isPartner", False)
        self.isAffiliate = data.get("roles", {}).get("isAffiliate", False)
        self.followers = data.get("followers", {}).get("totalCount", 0)
        self.lastBroadcast = Broadcast(data.get("lastBroadcast") or {})
        self.stream = Utils.getObject(Stream, data.get("stream"))

    def __str__(self):
        return "<Channel {}>".format(self.__dict__)

    def __repr__(self):
        return self.__str__()

class Broadcast:
    def __init__(self, data):
        self.id = data.get("id")
        self.title = Utils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.startedAt = TimeUtils.Datetime(data.get("startedAt"))

    def __str__(self):
        return "<Broadcast {}>".format(self.__dict__)

    def __repr__(self):
        return self.__str__()

class Stream:
    def __init__(self, data):
        self.id = data.get("id")
        self.title = Utils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.type = data.get("type") or ""
        self.previewImageURL = data.get("previewImageURL") or ""
        self.broadcaster = User(data.get("broadcaster") or {})
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.viewersCount = data.get("viewersCount", 0)

    def __str__(self):
        return "<Stream {}>".format(self.__dict__)

    def __repr__(self):
        return self.__str__()

class Video:
    def __init__(self, data):
        self.id = data.get("id")
        self.title = Utils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.previewThumbnailURL = data.get("previewThumbnailURL") or ""
        self.owner = User(data.get("owner") or {})
        self.creator = User(data.get("creator") or {})
        self.lengthSeconds = TimeUtils.Duration(data.get("lengthSeconds", 0))
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.publishedAt = TimeUtils.Datetime(data.get("publishedAt"))
        self.viewCount = data.get("viewCount", 0)

    def __str__(self):
        return "<Video {}>".format(self.__dict__)

    def __repr__(self):
        return self.__str__()

class Clip:
    def __init__(self, data):
        self.id = data.get("id")
        self.title = Utils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.thumbnailURL = data.get("thumbnailURL") or ""
        self.slug = data.get("slug") or ""
        self.url = data.get("url") or ""
        self.broadcaster = User(data.get("broadcaster") or {})
        self.curator = User(data.get("curator") or {})
        self.durationSeconds = TimeUtils.Duration(data.get("durationSeconds", 0))
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.viewCount = data.get("viewCount", 0)

    def __str__(self):
        return "<Clip {}>".format(self.__dict__)

    def __repr__(self):
        return self.__str__()

class Game:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name", "Unknown")
        self.boxArtURL = data.get("boxArtURL", "")
        self.displayName = data.get("displayName", self.name)

    def __str__(self):
        return "<Game {}>".format(self.__dict__)

    def __repr__(self):
        return self.__str__()