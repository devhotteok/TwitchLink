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
            return model(model.default)
        else:
            return model(data)

class User:
    default = {
        "id": None,
        "login": "Unknown",
        "displayName": "Unknown",
        "profileImageURL": None,
        "createdAt": "0001-01-01T00:00:00Z"
    }

    def __init__(self, data):
        self.id = data.get("id")
        self.login = data.get("login")
        self.displayName = data.get("displayName")
        self.profileImageURL = data.get("profileImageURL")
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt"))

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
        self.description = data.get("description")
        self.primaryColorHex = data.get("primaryColorHex")
        self.offlineImageURL = data.get("offlineImageURL")
        self.isPartner = data.get("roles").get("isPartner")
        self.isAffiliate = data.get("roles").get("isAffiliate")
        self.followers = data.get("followers").get("totalCount")
        self.stream = Utils.noneIfNone(data.get("stream"), Stream)

    def __str__(self):
        return "Channel Object " + str(self.__dict__)

class Stream:
    def __init__(self, data):
        self.id = data.get("id")
        self.title = data.get("title")
        self.game = Utils.defaultIfNone(data.get("game"), Game)
        self.type = data.get("type")
        self.previewImageURL = data.get("previewImageURL")
        self.broadcaster = User(data.get("broadcaster"))
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt"))
        self.viewersCount = data.get("viewersCount")

    def __str__(self):
        return "Stream Object " + str(self.__dict__)

class Video:
    def __init__(self, data):
        self.id = data.get("id")
        self.title = data.get("title")
        self.game = Utils.defaultIfNone(data.get("game"), Game)
        self.previewThumbnailURL = data.get("previewThumbnailURL")
        self.owner = Utils.defaultIfNone(data.get("owner"), User)
        self.creator = Utils.defaultIfNone(data.get("creator"), User)
        self.lengthSeconds = TwitchConfig.Duration(data.get("lengthSeconds"))
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt"))
        self.publishedAt = TwitchConfig.Datetime(data.get("publishedAt"))
        self.viewCount = data.get("viewCount")

    def __str__(self):
        return "Video Object " + str(self.__dict__)

class Clip:
    def __init__(self, data):
        self.id = data.get("id")
        self.title = data.get("title")
        self.game = Utils.defaultIfNone(data.get("game"), Game)
        self.thumbnailURL = data.get("thumbnailURL")
        self.slug = data.get("slug")
        self.url = data.get("url")
        self.broadcaster = Utils.defaultIfNone(data.get("broadcaster"), User)
        self.curator = Utils.defaultIfNone(data.get("curator"), User)
        self.durationSeconds = TwitchConfig.Duration(data.get("durationSeconds"))
        self.createdAt = TwitchConfig.Datetime(data.get("createdAt"))
        self.viewCount = data.get("viewCount")

    def __str__(self):
        return "Clip Object " + str(self.__dict__)

class Game:
    default = {
        "id": None,
        "name": "Unknown",
        "boxArtURL": "https://static-cdn.jtvnw.net/ttv-static/404_boxart-{width}x{height}.jpg",
        "displayName": "Unknown"
    }

    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name")
        self.boxArtURL = data.get("boxArtURL")
        self.displayName = data.get("displayName")

    def __str__(self):
        return "Game Object " + str(self.__dict__)