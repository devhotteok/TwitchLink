from datetime import datetime, timedelta


class TwitchConfig:
    class Datetime:
        def __init__(self, string):
            try:
                self.datetime = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                self.datetime = datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")

        def __str__(self):
            return self.datetime.__str__()

        def toUTC(self, UTC=None):
            if UTC == None:
                return self.datetime
            else:
                return self.datetime + timedelta(seconds=UTC.total_seconds())

        def date(self, UTC=None):
            return self.toUTC(UTC).date()

        def time(self, UTC=None):
            return self.toUTC(UTC).time()

    class Duration:
        def __init__(self, seconds):
            self.timedelta = timedelta(seconds=seconds)

        def __str__(self):
            return self.timedelta.__str__()

class Utils:
    @staticmethod
    def noneIfNone(data, model):
        if data == None:
            return None
        else:
            return model(data)

    @staticmethod
    def defaultIfNone(data, model):
        if data == None:
            return model({})
        else:
            return model(data)

class User:
    def __init__(self, data):
        self.id = data.get("id", None)
        self.login = data.get("login", "")
        self.displayName = data.get("displayName", self.login)
        self.profileImageURL = data.get("profileImageURL", None)
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt", "0001-01-01T00:00:00Z"))

    def formattedName(self):
        if self.id == None:
            return "Unknown User"
        if self.displayName == self.login:
            return self.displayName
        else:
            return "{}({})".format(self.displayName, self.login)

    def __str__(self):
        return "User Object " + str(self.__dict__)

class Channel(User):
    def __init__(self, data):
        super().__init__(data)
        self.description = data.get("description", "")
        self.primaryColorHex = data.get("primaryColorHex", "")
        self.offlineImageURL = data.get("offlineImageURL", None)
        self.isPartner = data.get("roles", {}).get("isPartner", False)
        self.isAffiliate = data.get("roles", {}).get("isAffiliate", False)
        self.followers = data.get("followers", {}).get("totalCount", 0)
        self.stream = Utils.noneIfNone(data.get("stream", None), Stream)

    def __str__(self):
        return "Channel Object " + str(self.__dict__)

class Stream:
    def __init__(self, data):
        self.id = data.get("id", None)
        self.title = data.get("title", "")
        self.game = Utils.defaultIfNone(data.get("game", None), Game)
        self.type = data.get("type", "")
        self.previewImageURL = data.get("previewImageURL", None)
        self.broadcaster = Utils.defaultIfNone(data.get("broadcaster", None), User)
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt", "0001-01-01T00:00:00Z"))
        self.viewersCount = data.get("viewersCount", 0)

    def __str__(self):
        return "Stream Object " + str(self.__dict__)

class Video:
    def __init__(self, data):
        self.id = data.get("id", None)
        self.title = data.get("title", "")
        self.game = Utils.defaultIfNone(data.get("game", None), Game)
        self.previewThumbnailURL = data.get("previewThumbnailURL", None)
        self.owner = Utils.defaultIfNone(data.get("owner", None), User)
        self.creator = Utils.defaultIfNone(data.get("creator", None), User)
        self.lengthSeconds = TwitchConfig.Duration(data.get("lengthSeconds", 0))
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt", "0001-01-01T00:00:00Z"))
        self.publishedAt = TwitchConfig.Datetime(data.get("publishedAt", "0001-01-01T00:00:00Z"))
        self.viewCount = data.get("viewCount", 0)

    def __str__(self):
        return "Video Object " + str(self.__dict__)

class Clip:
    def __init__(self, data):
        self.id = data.get("id", None)
        self.title = data.get("title", "")
        self.game = Utils.defaultIfNone(data.get("game", None), Game)
        self.thumbnailURL = data.get("thumbnailURL", None)
        self.slug = data.get("slug", "")
        self.url = data.get("url", "")
        self.broadcaster = Utils.defaultIfNone(data.get("broadcaster", None), User)
        self.curator = Utils.defaultIfNone(data.get("curator", None), User)
        self.durationSeconds = TwitchConfig.Duration(data.get("durationSeconds", 0))
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt", "0001-01-01T00:00:00Z"))
        self.viewCount = data.get("viewCount", 0)

    def __str__(self):
        return "Clip Object " + str(self.__dict__)

class Game:
    def __init__(self, data):
        self.id = data.get("id", None)
        self.name = data.get("name", "Unknown")
        self.boxArtURL = data.get("boxArtURL", "https://static-cdn.jtvnw.net/ttv-static/404_boxart-{width}x{height}.jpg")
        self.displayName = data.get("displayName", "Unknown")

    def __str__(self):
        return "Game Object " + str(self.__dict__)